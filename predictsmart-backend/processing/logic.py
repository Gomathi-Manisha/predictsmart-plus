import os
import pandas as pd
from prophet import Prophet
from pytrends.request import TrendReq
from geopy.distance import geodesic
import folium
from fpdf import FPDF
from fpdf import FPDF, XPos, YPos


def run_full_pipeline(sales_path, inventory_path, location_path, output_dir):
    # Step 1: Load input CSVs
    sales_df = pd.read_csv(sales_path)
    inventory_df = pd.read_csv(inventory_path)
    locations_df = pd.read_csv(location_path)

    # Step 2: Forecasting using Prophet
    forecast_df = []
    for (store, product), group in sales_df.groupby(['Store', 'Product']):
        group['Date'] = pd.to_datetime(group['Date'], format="%d-%m-%Y")
        ts_df = group.groupby('Date')['Units Sold'].sum().reset_index()
        ts_df.columns = ['ds', 'y']
        if len(ts_df) < 2:
            continue
        model = Prophet()
        model.fit(ts_df)
        future = model.make_future_dataframe(periods=7)
        forecast = model.predict(future)
        demand = round(forecast.iloc[-7:]['yhat'].sum())
        forecast_df.append({"Store": store, "Product": product, "Forecasted Demand": demand})

    forecast_df = pd.DataFrame(forecast_df)
    forecast_df.to_csv(os.path.join(output_dir, 'forecast_df.csv'), index=False)


    # Step 3: Trend boost using pytrends
    pytrends = TrendReq(hl='en-US', tz=330)
    keywords = forecast_df['Product'].unique().tolist()
    pytrends.build_payload(keywords, geo='IN', timeframe='today 1-m')
    trends_df = pytrends.interest_over_time().reset_index()
    latest_trend = trends_df.tail(1)[keywords].T.reset_index()
    latest_trend.columns = ['Product', 'TrendScore']

    forecast_df = forecast_df.merge(latest_trend, on='Product', how='left')
    forecast_df['TrendScore'].fillna(50, inplace=True)
    forecast_df['Boosted Demand'] = (
        forecast_df['Forecasted Demand'] * (1 + forecast_df['TrendScore'] / 100)
    ).round()

    # Step 4: Sourcing Engine with fallback + carbon impact
    recommendations = []
    fallback_coords = (22.0, 77.0)  # Generic fallback vendor location (India center)

    for _, row in forecast_df.iterrows():
        store = row['Store']
        product = row['Product']
        demand = row['Boosted Demand']

        try:
            stock = inventory_df[(inventory_df['Store'] == store) & (inventory_df['Product'] == product)]['Current Stock'].values[0]
        except IndexError:
            stock = 0

        if stock >= demand:
            continue

        deficit = demand - stock
        needy_coords = locations_df[locations_df['Store'] == store][['Latitude', 'Longitude']].values[0]

        candidates = inventory_df[
            (inventory_df['Product'] == product) &
            (inventory_df['Store'] != store) &
            (inventory_df['Current Stock'] > deficit)
        ]

        best = None
        min_dist = float('inf')

        for _, c in candidates.iterrows():
            source_store = c['Store']
            source_stock = c['Current Stock']
            try:
                source_coords = locations_df[locations_df['Store'] == source_store][['Latitude', 'Longitude']].values[0]
            except IndexError:
                continue
            dist = geodesic(needy_coords, source_coords).km
            if dist < min_dist:
                min_dist = dist
                best = {
                    'Product': product,
                    'Needy Store': store,
                    'Source Store': source_store,
                    'Distance (km)': round(dist, 2),
                    'Deficit': deficit,
                    'Source Stock': source_stock,
                    'Suggested Quantity': deficit,
                    'Carbon Impact (gCO2/km-unit)': round(0.3 * dist * deficit, 2)
                }

        if best is None:
            dist = geodesic(needy_coords, fallback_coords).km
            best = {
                'Product': product,
                'Needy Store': store,
                'Source Store': 'Fallback Vendor',
                'Distance (km)': round(dist, 2),
                'Deficit': deficit,
                'Source Stock': float('inf'),
                'Suggested Quantity': deficit,
                'Carbon Impact (gCO2/km-unit)': round(0.3 * dist * deficit, 2)
            }

        recommendations.append(best)

    rec_df = pd.DataFrame(recommendations)

    # Add cost and source type
    rec_df['Cost Multiplier'] = rec_df['Source Store'].apply(lambda x: 1.10 if x == 'Fallback Vendor' else 1.00)
    rec_df['Source Type'] = rec_df['Source Store'].apply(lambda x: 'External Vendor' if x == 'Fallback Vendor' else 'Internal Store')
    rec_df['Adjusted Cost per Unit'] = (50 * rec_df['Cost Multiplier']).round(2)

    # Save enhanced sourcing recommendations
    output_csv_path = os.path.join(output_dir, 'enhanced_sourcing_recommendations.csv')
    rec_df.to_csv(output_csv_path, index=False)

    # Step 5: Generate interactive map
    rec_df['Source Store'] = rec_df['Source Store'].str.strip().str.title()
    rec_df['Needy Store'] = rec_df['Needy Store'].str.strip().str.title()
    locations_df['Store'] = locations_df['Store'].str.strip().str.title()

    fallback_lat, fallback_lon = 23.2599, 77.4126
    m = folium.Map(location=[22.9734, 78.6569], zoom_start=5)

    for _, row in locations_df.iterrows():
        store = row['Store']
        lat, lon = row['Latitude'], row['Longitude']
        is_source = store in rec_df['Source Store'].values
        is_needy = store in rec_df['Needy Store'].values

        if is_needy and not is_source:
            icon = folium.Icon(color='red', icon='glyphicon glyphicon-alert')
        elif is_source and not is_needy:
            icon = folium.Icon(color='green', icon='glyphicon glyphicon-transfer')
        elif is_source and is_needy:
            icon = folium.Icon(color='orange', icon='glyphicon glyphicon-refresh')
        else:
            icon = folium.Icon(color='blue')

        folium.Marker([lat, lon], popup=store, icon=icon).add_to(m)

    if 'Fallback Vendor' in rec_df['Source Store'].values:
        folium.Marker(
            [fallback_lat, fallback_lon],
            popup='Fallback Vendor (External)',
            icon=folium.Icon(color='blue', icon='glyphicon glyphicon-shopping-cart')
        ).add_to(m)

    for _, row in rec_df.iterrows():
        src = row['Source Store']
        dst = row['Needy Store']
        product = row['Product']
        qty = row['Suggested Quantity']
        deficit = row['Deficit']
        cost = row.get('Adjusted Cost per Unit (₹)', 50)
        source_type = row.get('Source Type', 'Internal Store')

        if src == 'Fallback Vendor':
            coords1 = [fallback_lat, fallback_lon]
        elif src in locations_df['Store'].values:
            coords1 = locations_df[locations_df['Store'] == src][['Latitude', 'Longitude']].values[0]
        else:
            continue

        if dst not in locations_df['Store'].values:
            continue

        coords2 = locations_df[locations_df['Store'] == dst][['Latitude', 'Longitude']].values[0]
        color = 'red' if deficit >= 100 else 'orange' if deficit >= 50 else 'green'
        tooltip = f"{product}: {qty} units\nSource: {src} ({source_type})\nCost/unit: ₹{cost}"

        folium.PolyLine(
            [coords1, coords2],
            color=color,
            weight=5,
            tooltip=tooltip,
            popup=f"{product} | Qty: {qty} | Deficit: {deficit} | ₹{cost}/unit"
        ).add_to(m)

    legend = """
    <div style="position: fixed; bottom: 40px; left: 40px; width: 300px; height: 240px;
         background-color: white; z-index:9999; font-size:14px;
         border:2px solid grey; padding: 10px;">
    <b>Legend:</b><br>
    <span style="color:red;">■</span> Needy Store<br>
    <span style="color:green;">■</span> Source Store<br>
    <span style="color:orange;">■</span> Both Roles<br>
    <span style="color:blue;">■</span> Fallback Vendor (External)<br><br>
    <b>Arrows:</b><br>
    <span style="color:red;">▬</span> Urgent (≥ 100)<br>
    <span style="color:orange;">▬</span> Moderate (50–99)<br>
    <span style="color:green;">▬</span> Minor (&lt; 50)
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend))
    map_path = os.path.join(output_dir, 'sourcing_map_with_legend.html')
    m.save(map_path)

# Step 6: Generate PDF report
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=8)
    pdf.cell(200, 10, txt="Sourcing Recommendation Report", ln=True, align='C')
    pdf.ln(5)

    for col in rec_df.columns:
        pdf.cell(30, 8, col, border=1)
    pdf.ln()

    for _, row in rec_df.iterrows():
        for val in row:
            val = str(val).replace("∞", "INF")
            pdf.cell(30, 8, val[:28], border=1)
        pdf.ln()

    pdf_path = os.path.join(output_dir, 'sourcing_recommendation_report.pdf')
    pdf.output(pdf_path)
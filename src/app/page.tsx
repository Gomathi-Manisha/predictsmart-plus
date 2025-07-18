'use client';

import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { ReloadIcon } from '@radix-ui/react-icons';
import { motion } from 'framer-motion';
import { BarChart2, FileText, MapPin, Send, Table, Pencil } from 'lucide-react';
import dynamic from 'next/dynamic';

interface ReportLinks {
  forecast_csv: string;
  recommendation_csv: string;
  pdf_report: string;
  map_html: string;
}

const ForecastChart = dynamic(() => import('@/components/ForecastChart'), { ssr: false });

export default function UploadPage() {
  const [salesFile, setSalesFile] = useState<File | null>(null);
  const [inventoryFile, setInventoryFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [reportLinks, setReportLinks] = useState<ReportLinks | null>(null);
  const emailRef = useRef<HTMLInputElement>(null);

  const handleSubmit = async () => {
    if (!salesFile || !inventoryFile) return alert('Please upload both files.');
    const formData = new FormData();
    formData.append('sales_file', salesFile);
    formData.append('inventory_file', inventoryFile);

    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/process/', {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) throw new Error('Failed to process');
      const data: ReportLinks = await res.json();
      setReportLinks(data);
    } catch (err) {
      console.error(err);
      alert('Error processing files');
    } finally {
      setLoading(false);
    }
  };

  const handleSendEmail = async () => {
    const email = emailRef.current?.value;
    if (!email || !reportLinks?.pdf_report) return alert('Enter a valid email and ensure PDF is generated.');
    try {
      await fetch('http://localhost:8000/send-email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, file_path: reportLinks.pdf_report }),
      });
      alert('Email sent!');
    } catch (err) {
      console.error(err);
      alert('Failed to send email');
    }
  };

  const AnimatedButton = motion.a;

  return (
    <motion.div 
      className="min-h-screen bg-gradient-to-br from-[#E3F2FD] to-[#FFF8E1] text-gray-900 p-6"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 1.2 }}
    >
      <div className="max-w-6xl mx-auto space-y-12">
        <motion.h1 
          className="text-5xl font-bold text-center text-[#0D47A1] drop-shadow-md"
          initial={{ y: -30, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.3, duration: 1 }}
        >
          PredictSmart+ Data Upload Portal
        </motion.h1>

        <motion.div
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.6, duration: 1 }}
        >
          <Card className="shadow-2xl rounded-3xl border-0">
            <CardContent className="space-y-8 p-10 bg-white rounded-3xl">
              <motion.div className="space-y-3" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.7 }}>
                <Label className="text-base font-medium text-gray-700">Sales CSV</Label>
                <Input type="file" accept=".csv" onChange={(e) => e.target.files?.[0] && setSalesFile(e.target.files[0])} />
              </motion.div>
              <motion.div className="space-y-3" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.8 }}>
                <Label className="text-base font-medium text-gray-700">Inventory CSV</Label>
                <Input type="file" accept=".csv" onChange={(e) => e.target.files?.[0] && setInventoryFile(e.target.files[0])} />
              </motion.div>
              <Button onClick={handleSubmit} disabled={loading} size="lg" className="w-full bg-[#0D47A1] hover:bg-[#1565C0] text-lg font-bold">
                {loading ? <><ReloadIcon className="mr-2 h-5 w-5 animate-spin" /> Processing...</> : <>📤 Submit & Generate Insights</>}
              </Button>
            </CardContent>
          </Card>
        </motion.div>

        {reportLinks && (
          <motion.div
            className="space-y-10 bg-white rounded-3xl shadow-2xl p-10"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.9, duration: 1 }}
          >
            <div className="grid gap-6 grid-cols-1 sm:grid-cols-2 md:grid-cols-4">
              <AnimatedButton href={`http://localhost:8000${reportLinks.forecast_csv}`} download whileHover={{ scale: 1.05 }} className="bg-[#BBDEFB] hover:bg-[#90CAF9] text-[#0D47A1] font-bold text-lg px-6 py-8 rounded-2xl shadow-xl flex flex-col items-center">
                <Table size={32} />
                <span className="mt-2">Forecast CSV</span>
              </AnimatedButton>
              <AnimatedButton href={`http://localhost:8000${reportLinks.recommendation_csv}`} download whileHover={{ scale: 1.05 }} className="bg-[#BBDEFB] hover:bg-[#90CAF9] text-[#0D47A1] font-bold text-lg px-6 py-8 rounded-2xl shadow-xl flex flex-col items-center">
                <BarChart2 size={32} />
                <span className="mt-2">Recommendations CSV</span>
              </AnimatedButton>
              <AnimatedButton href={`http://localhost:8000${reportLinks.pdf_report}`} download target="_blank" rel="noopener noreferrer" whileHover={{ scale: 1.05 }} className="bg-[#FFF59D] hover:bg-[#FFF176] text-[#F57F17] font-bold text-lg px-6 py-8 rounded-2xl shadow-xl flex flex-col items-center">
                <FileText size={32} />
                <span className="mt-2">PDF Report</span>
              </AnimatedButton>
              <AnimatedButton href={`http://localhost:8000${reportLinks.map_html}`} target="_blank" whileHover={{ scale: 1.05 }} className="bg-[#B2DFDB] hover:bg-[#80CBC4] text-[#004D40] font-bold text-lg px-6 py-8 rounded-2xl shadow-xl flex flex-col items-center">
                <MapPin size={32} />
                <span className="mt-2">Interactive Map</span>
              </AnimatedButton>
            </div>

            <div className="pt-8">
              <h2 className="text-2xl font-semibold text-[#0D47A1]">Demand Forecast Dashboard</h2>
              <div className="mt-4">
                <ForecastChart />
              </div>
            </div>

            <div className="pt-8">
              <h2 className="text-2xl font-semibold text-[#0D47A1]">Send Report via Email</h2>
              <div className="flex gap-4 max-w-xl mt-3">
                <Input ref={emailRef} placeholder="Enter seller email" className="flex-1" />
                <Button onClick={handleSendEmail} className="bg-[#FBC02D] hover:bg-[#F9A825] text-white font-bold text-lg px-6 py-4">
                  <Send className="inline-block mr-2" size={20} /> Send PDF
                </Button>
              </div>
            </div>

            

            
            

            

          </motion.div>
        )}
      </div>
    </motion.div>
  );
}

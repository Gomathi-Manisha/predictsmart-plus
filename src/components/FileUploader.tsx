// app/page.tsx
'use client';
import React, { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import Papa from "papaparse";

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [parsedData, setParsedData] = useState<any[]>([]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0] || null;
    setFile(selectedFile);
  };

  const handleParse = () => {
    if (!file) return;
    Papa.parse(file, {
      header: true,
      skipEmptyLines: true,
      complete: (results) => {
        setParsedData(results.data);
      },
    });
  };

  return (
    <main className="min-h-screen bg-zinc-100 p-10">
      <h1 className="text-3xl font-bold mb-6 text-center">📦 PredictSmart+ Sourcing Optimizer</h1>

      <Card className="max-w-3xl mx-auto shadow-lg">
        <CardContent className="p-6">
          <div className="space-y-4">
            <div>
              <Label htmlFor="file-upload">Upload CSV File</Label>
              <Input
                id="file-upload"
                type="file"
                accept=".csv"
                onChange={handleFileChange}
              />
            </div>
            <Button onClick={handleParse} disabled={!file} className="w-full">
              Parse and Preview
            </Button>
          </div>
        </CardContent>
      </Card>

      {parsedData.length > 0 && (
        <div className="mt-10 overflow-auto">
          <h2 className="text-xl font-semibold mb-2 text-center">📄 CSV Preview</h2>
          <div className="overflow-x-auto border rounded-md bg-white">
            <table className="min-w-full text-sm text-left border-collapse">
              <thead className="bg-zinc-200">
                <tr>
                  {Object.keys(parsedData[0]).map((key) => (
                    <th key={key} className="p-3 border-b font-medium">
                      {key}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {parsedData.slice(0, 10).map((row, i) => (
                  <tr key={i} className="even:bg-zinc-50">
                    {Object.values(row).map((val, j) => (
                      <td key={j} className="p-3 border-b">
                        {val as string}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="text-xs text-center text-zinc-600 p-2">
              Showing first 10 rows only
            </div>
          </div>
        </div>
      )}
    </main>
  );
}

import React, { useEffect, useState } from 'react';

export default function Dashboard() {
  const [metrics, setMetrics] = useState(null);

  useEffect(() => {
    fetch('/api/dashboard_metrics')
      .then(res => res.json())
      .then(data => setMetrics(data));
  }, []);

  if (!metrics) return <p className="p-6">Loading...</p>;

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-4">📦 Inventory Dashboard</h1>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="bg-white shadow-lg p-4 rounded-2xl">
          <h2 className="text-lg font-semibold">📊 Total SKUs</h2>
          <p className="text-2xl text-blue-600">{metrics.total_skus}</p>
        </div>
        <div className="bg-white shadow-lg p-4 rounded-2xl">
          <h2 className="text-lg font-semibold">📉 Low Stock Items</h2>
          <p className="text-2xl text-red-500">{metrics.low_stock}</p>
        </div>
        <div className="bg-white shadow-lg p-4 rounded-2xl">
          <h2 className="text-lg font-semibold">🏢 Branches</h2>
          <p className="text-2xl">{metrics.branches.join(', ')}</p>
        </div>
      </div>
    </div>
  );
}

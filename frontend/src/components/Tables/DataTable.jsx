import React from 'react';

export default function DataTable({ columns, data }) {
  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.87rem' }}>
        <thead>
          <tr style={{ background: '#f5f6fa' }}>
            {columns.map((col) => (
              <th key={col} style={{ padding: '10px 14px', textAlign: 'left', color: '#555', fontWeight: 600, borderBottom: '2px solid #eee' }}>{col}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, i) => (
            <tr key={i} style={{ borderBottom: '1px solid #f0f0f0' }}>
              {columns.map((col) => (
                <td key={col} style={{ padding: '10px 14px', color: '#333' }}>{row[col]}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

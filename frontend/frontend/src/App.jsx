import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Analytics from "./pages/Analytics";
import Products from "./pages/Products";
import Customers from "./pages/Customers";
import DataQuality from "./pages/DataQuality";
import Exceptions from "./pages/Exceptions";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/products" element={<Products />} />
        <Route path="/customers" element={<Customers />} />
        <Route path="/data-quality" element={<DataQuality />} />
        <Route path="/exceptions" element={<Exceptions />} />
      </Routes>
    </Router>
  );
}

export default App;
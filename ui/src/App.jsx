import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import SpecParser from './pages/SpecParser';
import RiskScorer from './pages/RiskScorer';
import TestGenerator from './pages/TestGenerator';
import Reports from './pages/Reports';
import Guide from './pages/Guide';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/guide" element={<Guide />} />
          <Route path="/parse" element={<SpecParser />} />
          <Route path="/risk" element={<RiskScorer />} />
          <Route path="/generate" element={<TestGenerator />} />
          <Route path="/report" element={<Reports />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

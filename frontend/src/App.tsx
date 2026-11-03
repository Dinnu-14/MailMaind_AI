import { useEffect, useRef } from "react";
import { Route, Routes, useNavigate } from "react-router-dom";
import { useApp } from "./context/AppContext";
import AppLayout from "./layouts/AppLayout";
import Assistant from "./pages/Assistant";
import Categories from "./pages/Categories";
import Dashboard from "./pages/Dashboard";
import EmailDetail from "./pages/EmailDetail";
import Inbox from "./pages/Inbox";
import Settings from "./pages/Settings";

export default function App() {
  const { prefs } = useApp();
  const navigate = useNavigate();
  const done = useRef(false);

  // First visit: land on the chatbot so it can ask about the user's profession.
  useEffect(() => {
    if (prefs && !done.current) {
      done.current = true;
      if (!prefs.onboarded && window.location.pathname === "/") navigate("/assistant", { replace: true });
    }
  }, [prefs, navigate]);

  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<Dashboard />} />
        <Route path="priority" element={<Inbox mode="priority" />} />
        <Route path="all" element={<Inbox mode="all" />} />
        <Route path="email/:id" element={<EmailDetail />} />
        <Route path="assistant" element={<Assistant />} />
        <Route path="categories" element={<Categories />} />
        <Route path="settings" element={<Settings />} />
        <Route path="*" element={<Dashboard />} />
      </Route>
    </Routes>
  );
}

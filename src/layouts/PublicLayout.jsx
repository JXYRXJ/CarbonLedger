import { Outlet } from "react-router-dom";
import Navbar from "@/components/landing/Navbar.jsx";
import Footer from "@/components/landing/Footer.jsx";

export default function PublicLayout() {
  return (
    <div className="flex min-h-dvh flex-col bg-background">
      <Navbar />
      <main className="flex-1">
        <Outlet />
      </main>
      <Footer />
    </div>
  );
}

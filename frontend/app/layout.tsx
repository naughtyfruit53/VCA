import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "VCA Admin",
  description: "Voice AI Agent Platform - Admin Dashboard",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}

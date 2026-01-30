import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "RAM-US — Запчасти и тюнинг для американских авто",
  description:
    "Запчасти и тюнинг для RAM / Dodge / Jeep / Chrysler. Подбор по VIN, доставка по РФ, удобный заказ через Telegram.",
  metadataBase: new URL("https://ram-us.example"),
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ru">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased selection:bg-red-500/30 selection:text-white`}
      >
        {children}
      </body>
    </html>
  );
}

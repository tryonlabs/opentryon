import type { Metadata } from "next";
import { Geist, Geist_Mono, Lato, Roboto, Open_Sans, Mulish, Baloo_2, Readex_Pro } from "next/font/google";
import "./globals.css";
import { ThemeWrapper } from "../components/ThemeWrapper";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

const lato = Lato({
  weight: ['100', '300', '400', '700', '900'],
  subsets: ["latin"],
  variable: "--font-lato",
});

const roboto = Roboto({
  weight: ['100', '300', '400', '500', '700', '900'],
  subsets: ["latin"],
  variable: "--font-roboto",
});

const openSans = Open_Sans({
  weight: ['300', '400', '500', '600', '700', '800'],
  subsets: ["latin"],
  variable: "--font-open-sans",
});

const mulish = Mulish({
  weight: ['200', '300', '400', '500', '600', '700', '800', '900'],
  subsets: ["latin"],
  variable: "--font-mulish",
});

const baloo2 = Baloo_2({
  weight: ['400', '500', '600', '700', '800'],
  subsets: ["latin"],
  variable: "--font-baloo",
});

const readexPro = Readex_Pro({
  weight: ['200', '300', '400', '500', '600', '700'],
  subsets: ["latin"],
  variable: "--font-readex-pro",
});

export const metadata: Metadata = {
  title: "Tryon Agent AI",
  description: "Tryon Agent AI Home Page",
  viewport: {
    width: 'device-width',
    initialScale: 1,
    maximumScale: 5,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} ${lato.variable} ${roboto.variable} ${openSans.variable} ${mulish.variable} ${baloo2.variable} ${readexPro.variable} antialiased`}
      >
        <ThemeWrapper>
          {children}
        </ThemeWrapper>
      </body>
    </html>
  );
}

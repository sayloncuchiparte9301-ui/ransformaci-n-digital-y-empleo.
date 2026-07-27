import "./globals.css";

export const metadata = {
  title: "Transformación digital y empleo",
  description: "Dashboard del proyecto multiagéntico",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}

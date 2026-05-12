import type { Metadata } from "next";
import "@/styles/globals.css";

export const metadata: Metadata = {
  title: "Tech0 Search — 新規事業判断支援",
  description: "アイデア入力から GO/NO 判定までを可視化する暫定実装",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ja">
      <body>{children}</body>
    </html>
  );
}

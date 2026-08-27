import "./globals.css";

export const metadata = {
  title: "CartMate",
  description: "AI 이커머스 쇼핑 에이전트 데모",
};

export default function RootLayout({ children }) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}

import Link from "next/link";

export default function Home() {
  return (
    <div className="container">
      <h1>CartMate</h1>
      <p>AI 쇼핑 에이전트 데모</p>
      <div className="home-links">
        <Link href="/login">로그인</Link>
        <Link href="/signup">회원가입</Link>
        <Link href="/chat">채팅으로 바로가기</Link>
      </div>
    </div>
  );
}

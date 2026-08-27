"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiFetch, setToken } from "../../lib/api";

export default function SignupPage() {
  const router = useRouter();
  const [step, setStep] = useState("signup"); // "signup" | "verify"
  const [form, setForm] = useState({ name: "", email: "", password: "", phone: "" });
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(false);

  function update(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleSignup(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await apiFetch("/auth/signup", { method: "POST", body: JSON.stringify(form) });
      setNotice("인증코드를 발송했습니다. (서버 콘솔 로그에서 확인)");
      setStep("verify");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleVerify(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await apiFetch("/auth/signup/verify", {
        method: "POST",
        body: JSON.stringify({ email: form.email, code }),
      });
      setToken(data.access_token);
      router.push("/chat");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleResend() {
    setError("");
    try {
      await apiFetch("/auth/signup/resend", {
        method: "POST",
        body: JSON.stringify({ email: form.email }),
      });
      setNotice("인증코드를 다시 발송했습니다.");
    } catch (err) {
      setError(err.message);
    }
  }

  if (step === "verify") {
    return (
      <div className="container">
        <h1>이메일 인증</h1>
        {notice && <p style={{ fontSize: 13 }}>{notice}</p>}
        <form onSubmit={handleVerify}>
          <div className="field">
            <label>인증코드 (6자리)</label>
            <input value={code} onChange={(e) => setCode(e.target.value)} maxLength={6} required />
          </div>
          {error && <p className="error">{error}</p>}
          <button type="submit" className="btn-block" disabled={loading}>
            {loading ? "확인 중..." : "인증"}
          </button>
        </form>
        <p style={{ marginTop: 12, fontSize: 13, textAlign: "center" }}>
          코드를 못 받으셨나요?{" "}
          <button type="button" className="link-button" onClick={handleResend}>
            재발송
          </button>
        </p>
      </div>
    );
  }

  return (
    <div className="container">
      <h1>회원가입</h1>
      <form onSubmit={handleSignup}>
        <div className="field">
          <label>이름</label>
          <input value={form.name} onChange={(e) => update("name", e.target.value)} required />
        </div>
        <div className="field">
          <label>이메일</label>
          <input
            type="email"
            value={form.email}
            onChange={(e) => update("email", e.target.value)}
            required
          />
        </div>
        <div className="field">
          <label>비밀번호</label>
          <input
            type="password"
            value={form.password}
            onChange={(e) => update("password", e.target.value)}
            required
          />
        </div>
        <div className="field">
          <label>전화번호 (010-0000-0000)</label>
          <input value={form.phone} onChange={(e) => update("phone", e.target.value)} required />
        </div>
        {error && <p className="error">{error}</p>}
        <button type="submit" className="btn-block" disabled={loading}>
          {loading ? "가입 중..." : "가입하기"}
        </button>
      </form>
      <p style={{ marginTop: 12, fontSize: 13, textAlign: "center" }}>
        이미 계정이 있나요? <a href="/login">로그인</a>
      </p>
    </div>
  );
}

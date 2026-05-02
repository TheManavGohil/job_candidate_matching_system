import { redirect } from "next/navigation";
// Login is not needed in no-auth mode — redirect to dashboard
export default function LoginPage() {
  redirect("/dashboard");
}

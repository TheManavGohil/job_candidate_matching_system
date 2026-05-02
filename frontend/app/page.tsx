"use client";

import dynamic from 'next/dynamic';
import { useRouter } from 'next/navigation';

const ContainerScroll = dynamic(() => import('@/components/containerScroll').then(m => ({ default: m.ContainerScroll })), { ssr: false });
const RadialOrbitalTimeline = dynamic(() => import('@/components/orbitalTimeline'), { ssr: false });
import {
  ShieldCheck,
  Scale,
  Server,
  Rocket,
  Home as HomeIcon,
  Briefcase,
  Users,
  Search,
  Cpu,
  BarChart3,
  FileText,
  ArrowRight,
  Sparkles,
  Layers,
} from 'lucide-react';
import { NavBar } from '@/components/ui/navbar';
import { Button } from '@/components/ui/button';
import Link from 'next/link';

export default function Home() {
  const router = useRouter();

  const navItems = [
    { name: 'Home', url: '/', icon: HomeIcon },
    { name: 'Jobs', url: '/dashboard', icon: Briefcase },
    { name: 'Candidates', url: '/candidates', icon: Users },
  ];

  const timelineData = [
    {
      id: 1,
      title: 'Smart JD Parsing',
      date: '2026-02-01',
      content:
        'Automatically extract skills, responsibilities, and qualifications from any Job Description using advanced LLMs.',
      category: 'Parsing',
      icon: Search,
      relatedIds: [2],
      status: 'completed' as const,
      energy: 90,
    },
    {
      id: 2,
      title: 'Vector Matching Engine',
      date: '2026-02-02',
      content:
        'Match candidates to jobs semantically using state-of-the-art embedding models and vector search.',
      category: 'Engine',
      icon: Server,
      relatedIds: [1, 3],
      status: 'completed' as const,
      energy: 95,
    },
    {
      id: 3,
      title: 'Explainable AI Insights',
      date: '2026-02-03',
      content:
        'Get clear, section-by-section reasoning for why a candidate matches a job role.',
      category: 'Insights',
      icon: Rocket,
      relatedIds: [2],
      status: 'completed' as const,
      energy: 80,
    },
  ];

  return (
    <>
      {/* ─── Top Navigation ─── */}
      <div className="fixed top-0 left-0 right-0 z-50 flex justify-center items-center pointer-events-none">
        <div className="w-full max-w-7xl px-6 flex justify-between items-center pointer-events-auto">
          {/* Logo */}
          <div className="pt-6 font-bold text-xl flex items-center gap-2.5 text-slate-900">
            <div className="w-9 h-9 bg-gradient-to-br from-sky-600 to-cyan-500 rounded-lg flex items-center justify-center text-white text-sm font-extrabold shadow-md shadow-sky-200/50">
              M
            </div>
            <span className="tracking-tight">
              Match<span className="text-sky-600">IQ</span>
            </span>
          </div>

          {/* Center Nav */}
          <NavBar items={navItems} className="static translate-x-0 mb-0 pt-6" />

          {/* CTA */}
          <div className="pt-6 flex items-center gap-3">
            <Link href="/dashboard">
              <Button
                size="sm"
                className="rounded-full bg-sky-600 hover:bg-sky-700 text-white border-none cursor-pointer shadow-md shadow-sky-200/50 px-5"
              >
                Go to Dashboard
                <ArrowRight size={14} className="ml-1" />
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* ─── Main Content ─── */}
      <main className="min-h-screen bg-white overflow-hidden">

        {/* ─── Hero Section ─── */}
        <section className="max-w-7xl mx-auto px-6 lg:px-8 flex flex-col lg:flex-row items-center gap-10 lg:gap-16 pt-32 pb-8">
          {/* Left: Hero Copy */}
          <div className="w-full lg:w-1/2 space-y-7">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-sky-50 border border-sky-100 rounded-full text-xs font-semibold text-sky-700">
              <Sparkles size={12} />
              AI-Powered Recruitment Engine
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-[3.5rem] font-extrabold tracking-tight text-slate-900 leading-[1.1]">
              Find the perfect match with{' '}
              <span className="bg-gradient-to-r from-sky-600 to-cyan-500 bg-clip-text text-transparent">
                Explainable AI.
              </span>
            </h1>

            <p className="text-slate-500 text-base sm:text-lg max-w-xl leading-relaxed">
              MatchIQ gives your recruitment team a powerful AI engine to rank
              candidates, providing transparent, section-by-section reasoning
              for every match.
            </p>

            <div className="flex items-center gap-4 pt-2">
              <Link href="/dashboard">
                <Button className="rounded-full bg-sky-600 hover:bg-sky-700 text-white px-7 py-5 text-sm font-semibold shadow-lg shadow-sky-200/50 cursor-pointer">
                  Get Started
                  <ArrowRight size={15} className="ml-1.5" />
                </Button>
              </Link>
              <Link href="/candidates">
                <Button
                  variant="outline"
                  className="rounded-full px-7 py-5 text-sm font-semibold border-slate-200 text-slate-700 hover:bg-slate-50 cursor-pointer"
                >
                  Upload Candidates
                </Button>
              </Link>
            </div>

            {/* Feature Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4">
              <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm hover:shadow-md hover:border-sky-200 transition-all duration-300">
                <div className="flex items-center gap-2.5 text-sm font-semibold text-slate-900">
                  <div className="w-8 h-8 rounded-lg bg-sky-50 flex items-center justify-center">
                    <Scale className="h-4 w-4 text-sky-600" />
                  </div>
                  Semantic Matching
                </div>
                <p className="mt-2.5 text-sm text-slate-500 leading-relaxed">
                  Go beyond keyword matching. Our AI understands context,
                  skills, and experience implicitly.
                </p>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm hover:shadow-md hover:border-sky-200 transition-all duration-300">
                <div className="flex items-center gap-2.5 text-sm font-semibold text-slate-900">
                  <div className="w-8 h-8 rounded-lg bg-emerald-50 flex items-center justify-center">
                    <ShieldCheck className="h-4 w-4 text-emerald-600" />
                  </div>
                  Total Transparency
                </div>
                <p className="mt-2.5 text-sm text-slate-500 leading-relaxed">
                  No black boxes. Get clear explanations for why a candidate
                  scored highly on specific requirements.
                </p>
              </div>
            </div>
          </div>

          {/* Right: Orbital Timeline Visual */}
          <div className="w-full lg:w-1/2 relative h-[500px]">
            <RadialOrbitalTimeline timelineData={timelineData} />
          </div>
        </section>

        {/* ─── How It Works ─── */}
        <section className="py-24 bg-slate-50/70">
          <div className="max-w-6xl mx-auto px-6 lg:px-8">
            <div className="text-center mb-16">
              <p className="text-sm font-semibold text-sky-600 uppercase tracking-wider mb-3">
                How It Works
              </p>
              <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 tracking-tight">
                From JD to ranked candidates in minutes
              </h2>
              <p className="mt-4 text-slate-500 max-w-2xl mx-auto text-base leading-relaxed">
                Upload job descriptions, add candidate resumes, and let the AI
                do the heavy lifting with full explainability.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {[
                {
                  step: '01',
                  icon: FileText,
                  color: 'sky',
                  title: 'Upload Job Description',
                  desc: 'Upload a PDF, DOCX, or paste text. Our LLM extracts structured requirements, skills, and qualifications automatically.',
                },
                {
                  step: '02',
                  icon: Users,
                  color: 'violet',
                  title: 'Add Candidates',
                  desc: 'Upload individual resumes or bulk CSV files. AI parses each one into structured, searchable profiles.',
                },
                {
                  step: '03',
                  icon: BarChart3,
                  color: 'emerald',
                  title: 'Run AI Matching',
                  desc: 'Semantic vector matching ranks every candidate with section-by-section scores and explainable reasoning.',
                },
              ].map(({ step, icon: Icon, color, title, desc }) => (
                <div
                  key={step}
                  className="relative bg-white rounded-2xl border border-slate-200 p-7 shadow-sm hover:shadow-lg hover:border-sky-200 transition-all duration-300 group"
                >
                  <div className="flex items-center gap-4 mb-4">
                    <div
                      className={`w-11 h-11 rounded-xl flex items-center justify-center ${
                        color === 'sky'
                          ? 'bg-sky-50 text-sky-600'
                          : color === 'violet'
                          ? 'bg-violet-50 text-violet-600'
                          : 'bg-emerald-50 text-emerald-600'
                      }`}
                    >
                      <Icon size={20} />
                    </div>
                    <span className="text-xs font-bold text-slate-300 tracking-widest">
                      STEP {step}
                    </span>
                  </div>
                  <h3 className="text-lg font-bold text-slate-900 mb-2">
                    {title}
                  </h3>
                  <p className="text-sm text-slate-500 leading-relaxed">
                    {desc}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ─── Features Grid ─── */}
        <section className="py-24">
          <div className="max-w-6xl mx-auto px-6 lg:px-8">
            <div className="text-center mb-16">
              <p className="text-sm font-semibold text-sky-600 uppercase tracking-wider mb-3">
                Features
              </p>
              <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 tracking-tight">
                Why Choose MatchIQ
              </h2>
              <p className="mt-4 text-slate-500 max-w-2xl mx-auto text-base leading-relaxed">
                Standardised resume parsing and semantic scoring for recruitment
                teams. Upload bulk candidates, define job requirements, and
                instantly find the best talent with defensible, explainable AI
                reasoning.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[
                {
                  icon: Cpu,
                  title: 'LLM-Powered Parsing',
                  desc: 'Advanced language models extract structured data from any resume or job description format.',
                },
                {
                  icon: Layers,
                  title: 'Vector Embeddings',
                  desc: 'FAISS-powered semantic search matches candidates beyond simple keyword overlap.',
                },
                {
                  icon: Scale,
                  title: 'Weighted Sections',
                  desc: 'Customise how much each JD section (skills, experience, qualifications) impacts the final score.',
                },
                {
                  icon: ShieldCheck,
                  title: 'Explainable Rankings',
                  desc: 'Every candidate gets a detailed breakdown with strengths, gaps, and an overall grade.',
                },
                {
                  icon: BarChart3,
                  title: 'Bulk Processing',
                  desc: 'Upload hundreds of resumes via CSV. Celery workers process them in parallel with real-time status.',
                },
                {
                  icon: Search,
                  title: 'Defensible Decisions',
                  desc: 'Audit-ready scoring with clear reasoning. No opaque black-box algorithms.',
                },
              ].map(({ icon: Icon, title, desc }, i) => (
                <div
                  key={i}
                  className="bg-white rounded-2xl border border-slate-200 p-6 hover:shadow-lg hover:border-sky-200 transition-all duration-300"
                >
                  <div className="w-10 h-10 rounded-xl bg-sky-50 flex items-center justify-center mb-4">
                    <Icon size={20} className="text-sky-600" />
                  </div>
                  <h3 className="text-base font-bold text-slate-900 mb-2">
                    {title}
                  </h3>
                  <p className="text-sm text-slate-500 leading-relaxed">
                    {desc}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ─── Container Scroll CTA ─── */}
        <section className="relative bg-slate-50/70">
          <ContainerScroll
            titleComponent={
              <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 tracking-tight mb-10">
                See your candidates{' '}
                <span className="bg-gradient-to-r from-sky-600 to-cyan-500 bg-clip-text text-transparent">
                  ranked instantly
                </span>
              </h2>
            }
          >
            <div className="h-full w-full flex flex-col items-center justify-center bg-white p-8 text-center">
              <div className="w-14 h-14 rounded-2xl bg-sky-50 flex items-center justify-center mb-6">
                <Sparkles size={28} className="text-sky-600" />
              </div>
              <h3 className="text-2xl font-bold text-slate-900 mb-3">
                AI-Powered Dashboard
              </h3>
              <p className="text-slate-500 max-w-lg text-sm leading-relaxed mb-6">
                Upload job descriptions, manage candidates, run semantic
                matching, and explore detailed XAI explanations — all from a
                single, clean interface.
              </p>
              <Link href="/dashboard">
                <Button className="rounded-full bg-sky-600 hover:bg-sky-700 text-white px-8 py-5 text-sm font-semibold shadow-lg shadow-sky-200/50 cursor-pointer">
                  Open Dashboard
                  <ArrowRight size={15} className="ml-1.5" />
                </Button>
              </Link>
            </div>
          </ContainerScroll>
        </section>

        {/* ─── Footer ─── */}
        <footer className="border-t border-slate-200 bg-white py-12">
          <div className="max-w-6xl mx-auto px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2.5 text-lg font-bold text-slate-900">
              <div className="w-8 h-8 bg-gradient-to-br from-sky-600 to-cyan-500 rounded-lg flex items-center justify-center text-white text-xs font-extrabold">
                M
              </div>
              Match<span className="text-sky-600">IQ</span>
            </div>
            <p className="text-sm text-slate-400">
              © 2026 MatchIQ. AI-Powered Candidate Matching Engine, by the thank Krish bhai
            </p>
          </div>
        </footer>
      </main>
    </>
  );
}

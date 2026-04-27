import { Link } from 'react-router-dom';
import { Briefcase, Users, Upload, ArrowRight, Zap, Target, BarChart3, Shield } from 'lucide-react';

const FEATURES = [
  {
    icon: Target,
    title: 'Multi-Facet Scoring',
    desc: 'Skills, experience, education, and contextual fit — all weighted and combined intelligently.',
  },
  {
    icon: Zap,
    title: 'AI-Powered Matching',
    desc: 'Sentence-transformer embeddings with FAISS vector search for semantic understanding.',
  },
  {
    icon: BarChart3,
    title: 'Detailed Explanations',
    desc: 'Human-readable strengths, weaknesses, and recommendations for every match.',
  },
  {
    icon: Shield,
    title: 'Scalable Architecture',
    desc: 'Built to handle 100k+ candidates with Redis caching and optimized pipelines.',
  },
];

export default function HomePage() {
  return (
    <div className="animate-fade-in">
      {/* Hero */}
      <section className="text-center py-16 px-4">
        <div className="max-w-3xl mx-auto">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 text-primary text-sm font-semibold mb-6">
            <Zap className="w-3.5 h-3.5" />
            AI-Powered Candidate Matching
          </div>
          <h1 className="text-4xl sm:text-5xl font-extrabold text-text mb-4 leading-tight">
            Find the <span className="text-primary">perfect match</span> for
            every role
          </h1>
          <p className="text-lg text-text-secondary mb-8 max-w-xl mx-auto">
            Upload job descriptions and candidate profiles. Our engine scores,
            ranks, and explains matches so you can hire with confidence.
          </p>
          <div className="flex flex-wrap justify-center gap-3">
            <Link to="/upload" className="btn btn-primary text-base px-6 py-3">
              <Upload className="w-4 h-4" />
              Start Uploading
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link to="/jobs" className="btn btn-secondary text-base px-6 py-3">
              <Briefcase className="w-4 h-4" />
              View Jobs
            </Link>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="max-w-5xl mx-auto px-4 pb-16">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          {FEATURES.map(({ icon: Icon, title, desc }, i) => (
            <div
              key={title}
              className="card animate-slide-up"
              style={{ animationDelay: `${i * 100}ms` }}
            >
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center mb-3">
                <Icon className="w-5 h-5 text-primary" />
              </div>
              <h3 className="text-base font-semibold text-text mb-1">{title}</h3>
              <p className="text-sm text-text-secondary">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Quick Actions */}
      <section className="max-w-5xl mx-auto px-4 pb-16">
        <h2 className="text-xl font-bold text-text mb-5">Quick Actions</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Link to="/upload" className="card group hover:border-primary/40 no-underline">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-indigo-100 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
                <Briefcase className="w-5 h-5 text-primary" />
              </div>
              <div>
                <p className="text-sm font-semibold text-text">Upload Job Description</p>
                <p className="text-xs text-text-secondary">PDF, DOCX, or text</p>
              </div>
            </div>
          </Link>

          <Link to="/upload" className="card group hover:border-primary/40 no-underline">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center group-hover:bg-accent/20 transition-colors">
                <Users className="w-5 h-5 text-amber-600" />
              </div>
              <div>
                <p className="text-sm font-semibold text-text">Upload Candidates</p>
                <p className="text-xs text-text-secondary">CSV or single resume</p>
              </div>
            </div>
          </Link>

          <Link to="/jobs" className="card group hover:border-primary/40 no-underline">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-emerald-100 flex items-center justify-center group-hover:bg-success/20 transition-colors">
                <BarChart3 className="w-5 h-5 text-emerald-600" />
              </div>
              <div>
                <p className="text-sm font-semibold text-text">Run Matching</p>
                <p className="text-xs text-text-secondary">Score & rank candidates</p>
              </div>
            </div>
          </Link>
        </div>
      </section>
    </div>
  );
}

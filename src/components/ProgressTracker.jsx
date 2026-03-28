import React, { useState, useEffect } from 'react';
import api from '../api';
import styles from './ProgressTracker.module.css';

// ── 12 Installment Phase Definitions ─────────────────────────────
const PHASES = [
  { id: 0,  name: "New Admission",               icon: "🎓", desc: "Initial enrollment support and registration fees" },
  { id: 1,  name: "Mid-Term Installment",         icon: "📚", desc: "Semester mid-point academic support" },
  { id: 2,  name: "Academic Renewal",             icon: "🔄", desc: "Annual enrollment renewal and re-admission" },
  { id: 3,  name: "Completion Status",            icon: "✅", desc: "Course completion milestone disbursement" },
  { id: 4,  name: "Study Material Support",       icon: "📖", desc: "Books, materials, and exam preparation resources" },
  { id: 5,  name: "Hostel / Living Expense",      icon: "🏠", desc: "Accommodation and daily living allowance" },
  { id: 6,  name: "Emergency Support",            icon: "🚨", desc: "Urgent financial assistance for crises" },
  { id: 7,  name: "Dropout Recovery Support",     icon: "🤝", desc: "Re-integration support after academic disruption" },
  { id: 8,  name: "Skill & Certification",        icon: "🏅", desc: "Professional skill building and certifications" },
  { id: 9,  name: "Device / Tech Support",        icon: "💻", desc: "Laptop, phone, or internet connectivity grant" },
  { id: 10, name: "Performance Incentive",        icon: "⭐", desc: "Merit-based reward for academic excellence" },
  { id: 11, name: "Special Category Support",     icon: "💙", desc: "Targeted support for differently-abled students" },
];

const fmt = (n) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(n);
const fmtDate = (iso) => iso ? new Date(iso).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }) : null;

// ── Dummy installments for demo mode ─────────────────────────────
function makeDummyInstallments(phasesCompleted = 4, amountPerStudent = 48000) {
  const perPhase = amountPerStudent / 12;
  return PHASES.map((p, i) => ({
    phase: p.id,
    phase_name: p.name,
    amount: perPhase,
    is_disbursed: i < phasesCompleted,
    disbursed_at: i < phasesCompleted ? new Date(Date.now() - (phasesCompleted - i) * 15 * 24 * 3600 * 1000).toISOString() : null,
    tx_hash: i < phasesCompleted ? `0x${Math.random().toString(16).slice(2, 12)}` : null,
  }));
}

export default function ProgressTracker({ application }) {
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [hoveredPhase, setHoveredPhase] = useState(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const res = await api.get(`/ngo/scholarships/${application.application_id}`);
        setDetail(res.data);
      } catch (err) {
        console.warn('Using demo data for progress tracker.', err);
        // Build demo detail from summary data
        setDetail({
          application_id: application.application_id,
          student_name: application.student_name,
          institution_name: "Delhi Technological University",
          course: "B.Tech Computer Science",
          annual_family_income: 180000,
          scheme_title: application.scheme_title,
          amount_per_student: application.amount_per_student,
          status: application.status,
          applied_at: application.applied_at,
          verified_by_genai: application.verified_by_genai,
          genai_result: application.verified_by_genai ? { valid: true, reason: "Documents verified successfully.", confidence: 0.96 } : null,
          installments: makeDummyInstallments(application.phases_completed, application.amount_per_student),
        });
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [application.application_id]);

  if (loading) {
    return (
      <div className={styles.loading}>
        <div className={styles.loadingSpinner} />
        <span>Loading scholarship tracker…</span>
      </div>
    );
  }

  if (!detail) return null;

  const completed = detail.installments.filter(i => i.is_disbursed).length;
  const totalDisbursed = detail.installments.filter(i => i.is_disbursed).reduce((s, i) => s + i.amount, 0);
  const progressPct = Math.round((completed / 12) * 100);

  return (
    <div className={styles.tracker}>
      {/* ── Student Info Card ──────────────────────────────────── */}
      <div className={styles.studentCard}>
        <div className={styles.studentAvatar}>{detail.student_name[0]}</div>
        <div className={styles.studentInfo}>
          <h2 className={styles.studentName}>{detail.student_name}</h2>
          <p className={styles.studentMeta}>{detail.institution_name} · {detail.course}</p>
          {detail.annual_family_income && (
            <p className={styles.studentIncome}>Annual Family Income: {fmt(detail.annual_family_income)}</p>
          )}
        </div>
        <div className={styles.studentStats}>
          <div className={styles.studentStat}>
            <span className={styles.statVal}>{fmt(detail.amount_per_student)}</span>
            <span className={styles.statLbl}>Total Award</span>
          </div>
          <div className={styles.studentStat}>
            <span className={styles.statVal}>{fmt(totalDisbursed)}</span>
            <span className={styles.statLbl}>Disbursed</span>
          </div>
          <div className={styles.studentStat}>
            <span className={styles.statVal}>{completed}/12</span>
            <span className={styles.statLbl}>Stages Done</span>
          </div>
        </div>
      </div>

      {/* ── GenAI Verification Banner ──────────────────────────── */}
      {detail.verified_by_genai !== null && (
        <div className={`${styles.verificationBanner} ${detail.verified_by_genai ? styles.verifiedBanner : styles.rejectedBanner}`}>
          {detail.verified_by_genai ? '✅' : '❌'}
          <span>
            <strong>AI Document Verification: {detail.verified_by_genai ? 'Passed' : 'Failed'}</strong>
            {detail.genai_result?.reason && ` — ${detail.genai_result.reason}`}
            {detail.genai_result?.confidence && ` (Confidence: ${Math.round(detail.genai_result.confidence * 100)}%)`}
          </span>
        </div>
      )}

      {/* ── Overall Progress Bar ───────────────────────────────── */}
      <div className={styles.progressSummary}>
        <div className={styles.progressHeader}>
          <span className={styles.progressTitle}>Scholarship Journey Progress</span>
          <span className={styles.progressPct}>{progressPct}%</span>
        </div>
        <div className={styles.progressBarTrack}>
          <div
            className={styles.progressBarFill}
            style={{ width: `${progressPct}%` }}
          />
        </div>
        <div className={styles.progressSub}>{completed} of 12 stages completed</div>
      </div>

      {/* ── 12-Stage Timeline ─────────────────────────────────── */}
      <div className={styles.timeline}>
        {detail.installments.map((inst, idx) => {
          const phase = PHASES[inst.phase] || PHASES[idx];
          const isDone = inst.is_disbursed;
          const isCurrent = !isDone && idx === completed;
          const isHovered = hoveredPhase === idx;

          return (
            <div
              key={inst.phase}
              className={`${styles.stageWrap} ${isDone ? styles.stageDone : ''} ${isCurrent ? styles.stageCurrent : ''}`}
              onMouseEnter={() => setHoveredPhase(idx)}
              onMouseLeave={() => setHoveredPhase(null)}
            >
              {/* Connector Line */}
              {idx < 11 && (
                <div className={`${styles.connector} ${isDone ? styles.connectorDone : ''}`} />
              )}

              {/* Stage Node */}
              <div className={`${styles.stageNode} ${isDone ? styles.nodeCompleted : ''} ${isCurrent ? styles.nodeCurrent : ''}`}>
                {isDone ? (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                    <path d="M5 12l5 5L19 7" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                ) : isCurrent ? (
                  <div className={styles.pulseRing} />
                ) : (
                  <span className={styles.stageNum}>{idx + 1}</span>
                )}
              </div>

              {/* Stage Card */}
              <div className={`${styles.stageCard} ${isHovered ? styles.stageCardHovered : ''}`}>
                <div className={styles.stageCardHeader}>
                  <span className={styles.stageEmoji}>{phase.icon}</span>
                  <div>
                    <div className={styles.stageName}>{phase.name}</div>
                    <div className={styles.stageAmount}>{fmt(inst.amount)}</div>
                  </div>
                  {isCurrent && <span className={styles.currentTag}>In Progress</span>}
                </div>

                {isHovered && (
                  <div className={styles.stageExpanded}>
                    <p className={styles.stageDesc}>{phase.desc}</p>
                    {isDone && inst.disbursed_at && (
                      <p className={styles.stageDisbDate}>
                        💸 Disbursed on {fmtDate(inst.disbursed_at)}
                      </p>
                    )}
                    {isDone && inst.tx_hash && (
                      <code className={styles.stageTxHash}>
                        Tx: {inst.tx_hash.slice(0, 14)}…
                      </code>
                    )}
                    {!isDone && !isCurrent && (
                      <p className={styles.stagePending}>⏳ Pending Disbursement</p>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

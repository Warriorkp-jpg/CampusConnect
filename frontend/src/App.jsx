import { useEffect, useState } from 'react';
import { Link, Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom';
import { api, downloadProtectedFile } from './api';
import { useAuth } from './AuthContext';

function Protected({ children, roles }) {
  const { user, loading } = useAuth();
  if (loading) return <ScreenLoader />;
  if (!user) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(user.role)) return <Navigate to="/" replace />;
  return children;
}

function ScreenLoader() {
  return <div className="loader-screen"><span className="spinner" />Loading CampusConnect…</div>;
}

function Brand({ compact = false }) {
  return <div className="brand"><span className="brand-mark">C</span>{!compact && <span>Campus<span className="brand-light">Connect</span></span>}</div>;
}

function AuthShell({ children, eyebrow, title, subtitle }) {
  return <main className="auth-page">
    <section className="auth-story">
      <Brand />
      <div className="story-copy">
        <span className="eyebrow">JMIT · PLACEMENT PORTAL</span>
        <h1>Make your next<br /><span>move count.</span></h1>
        <p>One place for students, recruiters and the placement team to move opportunities forward.</p>
      </div>
      <div className="story-footer">A smarter campus placement experience.</div>
    </section>
    <section className="auth-panel">
      <div className="auth-card">
        <span className="eyebrow">{eyebrow}</span>
        <h2>{title}</h2>
        <p className="muted">{subtitle}</p>
        {children}
      </div>
    </section>
  </main>;
}

function Login() {
  const { login, user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => { if (user) navigate('/'); }, [user, navigate]);

  async function submit(event) {
    event.preventDefault(); setError(''); setBusy(true);
    try { await login(username.trim(), password); navigate('/'); }
    catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }

  return <AuthShell eyebrow="WELCOME BACK" title="Sign in" subtitle="Use your student roll number or recruiter username.">
    {location.state?.notice && <div className="alert success">{location.state.notice}</div>}
    <form onSubmit={submit} className="form-stack">
      <label>Username / roll number<input value={username} onChange={e => setUsername(e.target.value)} autoComplete="username" required placeholder="e.g. JMIT2027CSE001" /></label>
      <label>Password<input type="password" value={password} onChange={e => setPassword(e.target.value)} autoComplete="current-password" required placeholder="Enter your password" /></label>
      {error && <div className="alert error">{error}</div>}
      <button className="btn primary full" disabled={busy}>{busy ? 'Signing in…' : 'Sign in'} <span>→</span></button>
    </form>
    <p className="auth-switch">New student? <Link to="/register">Create an account</Link></p><p className="auth-switch">Hiring team? <Link to="/register/recruiter">Register your company</Link></p>
  </AuthShell>;
}

function RecruiterRegister() {
  const [form,setForm] = useState({username:'',email:'',company_name:'',phone_number:'',password:''});
  const [error,setError] = useState('');
  const [busy,setBusy] = useState(false);
  const navigate = useNavigate();
  async function submit(event) {
    event.preventDefault();setError('');setBusy(true);
    try {
      await api('/register/recruiter/',{method:'POST',body:JSON.stringify(form)},false);
      navigate('/login',{state:{notice:'Recruiter account submitted. Wait for TPO approval before publishing drives.'}});
    } catch(err){setError(err.message);}
    finally{setBusy(false);}
  }
  return <AuthShell eyebrow="RECRUITER ONBOARDING" title="Register your company" subtitle="Create a recruiter account. The TPO will review and approve it before hiring tools are enabled.">
    <form className="form-stack" onSubmit={submit}>
      <label>Username<input required value={form.username} onChange={e=>setForm({...form,username:e.target.value})} autoComplete="username"/></label>
      <label>Company name<input required value={form.company_name} onChange={e=>setForm({...form,company_name:e.target.value})}/></label>
      <label>Work email<input type="email" required value={form.email} onChange={e=>setForm({...form,email:e.target.value})}/></label>
      <label>Phone number<input value={form.phone_number} onChange={e=>setForm({...form,phone_number:e.target.value})}/></label>
      <label>Password<input type="password" minLength={8} required value={form.password} onChange={e=>setForm({...form,password:e.target.value})} autoComplete="new-password"/></label>
      {error&&<div className="alert error">{error}</div>}
      <button className="btn primary full" disabled={busy}>{busy?'Submitting…':'Submit for TPO approval →'}</button>
    </form>
    <p className="auth-switch">Already have an account? <Link to="/login">Sign in</Link></p>
  </AuthShell>;
}

function Register() {
  const [step, setStep] = useState(1);
  const [rollNumber, setRollNumber] = useState('');
  const [challengeId, setChallengeId] = useState('');
  const [otp, setOtp] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();

  async function requestOtp(event) {
    event.preventDefault(); setError(''); setBusy(true);
    try {
      const result = await api('/register/student/request-otp/', { method: 'POST', body: JSON.stringify({ roll_number: rollNumber }) }, false);
      setChallengeId(result.challenge_id);
      setMessage(result.detail);
      setStep(2);
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }

  async function verifyOtp(event) {
    event.preventDefault(); setError(''); setBusy(true);
    try {
      const result = await api('/register/student/verify-otp/', { method: 'POST', body: JSON.stringify({ challenge_id: challengeId, otp }) }, false);
      setMessage(result.detail);
      setStep(3);
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }

  async function complete(event) {
    event.preventDefault(); setError('');
    if (password !== confirm) { setError('Passwords do not match.'); return; }
    setBusy(true);
    try {
      await api('/register/student/', { method: 'POST', body: JSON.stringify({ challenge_id: challengeId, password }) }, false);
      setMessage('Account created. You can now sign in with your roll number.');
      navigate('/login', { state: { notice: 'Registration successful. Sign in to continue.' } });
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }

  return <AuthShell eyebrow="STUDENT ONBOARDING" title="Create your account" subtitle="Your details are verified against the official JMIT student roster.">
    <div className="steps"><span className={step >= 1 ? 'active' : ''}>1 <small>Roll number</small></span><i /><span className={step >= 2 ? 'active' : ''}>2 <small>Email OTP</small></span><i /><span className={step >= 3 ? 'active' : ''}>3 <small>Password</small></span></div>
    {step === 1 && <form className="form-stack" onSubmit={requestOtp}>
      <label>College roll number<input value={rollNumber} onChange={e => setRollNumber(e.target.value.toUpperCase())} required placeholder="JMIT2027CSE001" /></label>
      <p className="hint">We'll send a verification code to the college email recorded by the TPO. You cannot change that email here.</p>
      <button className="btn primary full" disabled={busy}>{busy ? 'Sending…' : 'Send verification code →'}</button>
    </form>}
    {step === 2 && <form className="form-stack" onSubmit={verifyOtp}>
      <div className="alert info">{message}</div>
      <label>6-digit verification code<input inputMode="numeric" pattern="[0-9]{6}" maxLength={6} value={otp} onChange={e => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))} required placeholder="000000" /></label>
      <button className="btn primary full" disabled={busy || otp.length !== 6}>{busy ? 'Verifying…' : 'Verify email →'}</button>
      <button type="button" className="btn text-btn" onClick={() => setStep(1)}>Use another roll number</button>
    </form>}
    {step === 3 && <form className="form-stack" onSubmit={complete}>
      <div className="alert success">{message}</div>
      <label>Create password<input type="password" minLength={8} value={password} onChange={e => setPassword(e.target.value)} required autoComplete="new-password" /></label>
      <label>Confirm password<input type="password" minLength={8} value={confirm} onChange={e => setConfirm(e.target.value)} required autoComplete="new-password" /></label>
      <button className="btn primary full" disabled={busy}>{busy ? 'Creating account…' : 'Create student account →'}</button>
    </form>}
    {error && <div className="alert error">{error}</div>}
    <p className="auth-switch">Already registered? <Link to="/login">Sign in</Link></p>
  </AuthShell>;
}

function NotificationBell() {
  const [items,setItems] = useState([]);
  const [open,setOpen] = useState(false);
  const [error,setError] = useState('');
  async function load() {
    try { const result = await api('/notifications/'); setItems(safeList(result)); setError(''); }
    catch(err){setError(err.message);}
  }
  useEffect(()=>{load();},[]);
  const unread = items.filter(item=>!item.is_read).length;
  async function markRead(item) {
    if(item.is_read) return;
    try { await api(`/notifications/${item.id}/`,{method:'PATCH',body:JSON.stringify({is_read:true})}); await load(); }
    catch(err){setError(err.message);}
  }
  return <div className="notification-wrap">
    <button className="notification-trigger" onClick={()=>{setOpen(!open);if(!open)load();}} aria-label="Notifications">♧{unread>0&&<span>{unread>9?'9+':unread}</span>}</button>
    {open&&<div className="notification-popover"><div className="notification-head"><strong>Notifications</strong><button className="btn small" onClick={load}>Refresh</button></div>
      {error&&<p className="notification-error">{error}</p>}
      {items.length?items.slice(0,8).map(item=><button className={item.is_read?'notification-item':'notification-item unread'} key={item.id} onClick={()=>markRead(item)}><strong>{item.title}</strong><span>{item.message}</span><small>{new Date(item.created_at).toLocaleString()}</small></button>):<div className="empty compact">You're all caught up.</div>}
    </div>}
  </div>;
}

function AppLayout({ children }) {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);
  const roleLabel = user.role === 'TPO' ? 'Placement office' : user.role === 'RECRUITER' ? 'Recruiter workspace' : 'Student workspace';
  return <div className="app-shell">
    <aside className={menuOpen ? 'sidebar open' : 'sidebar'}>
      <Brand />
      <div className="side-label">WORKSPACE</div>
      <nav>
        <Link className={location.pathname === '/' ? 'selected' : ''} to="/"><span>▦</span> Overview</Link>
        <Link to="/" className="side-muted"><span>◷</span> {user.role === 'STUDENT' ? 'My applications' : user.role === 'TPO' ? 'Student roster' : 'My drives'}</Link>
      </nav>
      <div className="sidebar-bottom"><div className="avatar">{(user.first_name || user.username || 'U').slice(0,1).toUpperCase()}</div><div className="user-mini"><strong>{user.first_name || user.username}</strong><small>{roleLabel}</small></div><button className="icon-btn" onClick={logout} title="Sign out">↗</button></div>
    </aside>
    <main className="main-area">
      <header className="topbar"><button className="mobile-menu" onClick={() => setMenuOpen(!menuOpen)}>☰</button><div><span className="crumb">CampusConnect</span><span className="crumb-sep"> / </span><strong>{roleLabel}</strong></div><div className="topbar-right"><NotificationBell /><span className="status-dot" /> JMIT Campus</div></header>
      <div className="page-content">{children}</div>
    </main>
  </div>;
}

function PageHeader({ eyebrow, title, subtitle, action }) {
  return <div className="page-header"><div><span className="eyebrow">{eyebrow}</span><h1>{title}</h1><p>{subtitle}</p></div>{action}</div>;
}
function Stat({ label, value, note }) {
  return <div className="stat-card"><span>{label}</span><strong>{value ?? '—'}</strong><small>{note}</small></div>;
}
function DataTable({ columns, rows, empty = 'Nothing to show yet.' }) {
  return <div className="table-wrap">{rows.length ? <table><thead><tr>{columns.map(c => <th key={c.key}>{c.label}</th>)}</tr></thead><tbody>{rows.map((row, i) => <tr key={row.id ?? i}>{columns.map(c => <td key={c.key}>{c.render ? c.render(row) : (row[c.key] ?? '—')}</td>)}</tr>)}</tbody></table> : <div className="empty">{empty}</div>}</div>;
}
function Tag({ children, tone = '' }) { return <span className={`tag ${tone}`}>{children}</span>; }

function TpoDashboard() {
  const [stats, setStats] = useState(null);
  const [roster, setRoster] = useState([]);
  const [recruiters, setRecruiters] = useState([]);
  const [file, setFile] = useState(null);
  const [notice, setNotice] = useState('');
  const [importErrors, setImportErrors] = useState([]);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function load() {
    try {
      const [s, r, p] = await Promise.all([api('/tpo-zone/'), api('/tpo/student-roster/'), api('/tpo/recruiters/pending/')]);
      setStats(s); setRoster(safeList(r)); setRecruiters(safeList(p));
    } catch (err) { setError(err.message); }
  }
  useEffect(() => { load(); }, []);

  async function upload(event) {
    event.preventDefault(); if (!file) return;
    setBusy(true); setError(''); setNotice('');
    const form = new FormData(); form.append('file', file);
    try {
      const result = await api('/tpo/student-roster/import/', { method: 'POST', body: form });
      setNotice(`Imported ${result.created} students · skipped ${result.skipped_existing} existing · ${result.error_count} invalid rows.`);
      setImportErrors(result.errors || []);
      setFile(null); await load();
    } catch (err) { setError(err.message); }
    finally { setBusy(false); }
  }

  async function review(id, decision) {
    setError('');
    try { await api(`/tpo/recruiters/${id}/review/`, { method: 'PATCH', body: JSON.stringify({ recruiter_status: decision }) }); await load(); }
    catch (err) { setError(err.message); }
  }

  return <><PageHeader eyebrow="TPO CONTROL CENTRE" title="Placement overview" subtitle="Manage student onboarding, recruiter approvals and campus activity." action={<button className="btn" onClick={()=>downloadProtectedFile('/tpo/reports/applications.csv/','campusconnect-applications.csv').catch(err=>setError(err.message))}>Export report ↓</button>} />
    {error && <div className="alert error">{error}</div>}{notice && <div className="alert success">{notice}</div>}
    <div className="stats-grid"><Stat label="Registered students" value={stats?.registered_students} note="Active student accounts" /><Stat label="Roster records" value={stats?.roster_students} note="Official student list" /><Stat label="Pending recruiters" value={stats?.pending_recruiters} note="Awaiting TPO review" /><Stat label="Placement drives" value={stats?.total_drives} note={(stats?.active_drives ?? 0) + ' active'} /><Stat label="Applications" value={stats?.total_applications} note="Across all placement drives" /><Stat label="Placement rate" value={(stats?.placement_rate ?? 0) + '%'} note={(stats?.selected_students ?? 0) + ' students selected'} /></div><section className="stage-summary">{Object.entries(stats?.application_stages || {}).map(([stage,count])=><div key={stage}><span>{stage}</span><strong>{count}</strong></div>)}</section>
    <div className="content-grid">
      <section className="panel"><div className="panel-heading"><div><h3>Bulk student onboarding</h3><p>Upload the official CSV or Excel roster.</p></div><Tag tone="blue">CSV / XLSX</Tag></div>
        <form className="upload-box" onSubmit={upload}><label className="file-pick">＋ <span>{file ? file.name : 'Choose roster file'}</span><input type="file" accept=".csv,.xlsx" onChange={e => setFile(e.target.files?.[0] || null)} /></label><button className="btn primary" disabled={!file || busy}>{busy ? 'Importing…' : 'Import roster'}</button></form>
        <p className="hint">Required columns: roll_number, full_name, college_email. Existing records are never overwritten.</p>
        {importErrors.length>0&&<div className="import-errors"><strong>Rows needing correction</strong>{importErrors.slice(0,8).map(item=><div key={item.row}><b>Row {item.row} · {item.roll_number || 'No roll number'}</b><span>{item.errors.join('; ')}</span></div>)}{importErrors.length>8&&<small>And {importErrors.length-8} more invalid rows. Correct the file and upload again.</small>}</div>}
        <a className="inline-link" href="/student_roster_template.csv" target="_blank" rel="noreferrer">Download CSV template ↗</a>
      </section>
      <section className="panel"><div className="panel-heading"><div><h3>Recruiter approvals</h3><p>Only approved recruiters can publish drives.</p></div><Tag>{recruiters.length} pending</Tag></div>
        {recruiters.length ? recruiters.map(r => <div className="approval-row" key={r.id}><div><strong>{r.company_name}</strong><small>{r.email || r.username}</small></div><div className="row-actions"><button className="btn small primary" onClick={() => review(r.id, 'APPROVED')}>Approve</button><button className="btn small danger" onClick={() => review(r.id, 'REJECTED')}>Reject</button></div></div>) : <div className="empty compact">No pending recruiter approvals.</div>}
      </section>
    </div>
    <section className="panel section-gap"><div className="panel-heading"><div><h3>Student roster</h3><p>Official records used for student verification.</p></div><Tag>{roster.length} records</Tag></div>
      <DataTable columns={[{key:'roll_number',label:'Roll number'},{key:'full_name',label:'Student name'},{key:'college_email',label:'College email'},{key:'cgpa',label:'CGPA'},{key:'backlogs',label:'Backlogs'},{key:'student_user',label:'Account',render:r=>r.student_user ? <Tag tone="green">Registered</Tag> : <Tag tone="amber">Not registered</Tag>}]} rows={roster} />
    </section>
  </>;
}

function StudentProfilePanel() {
  const { user } = useAuth();
  const [profile,setProfile] = useState({skills:'',github_url:'',linkedin_url:'',resume_uploaded:false});
  const [resume,setResume] = useState(null);
  const [notice,setNotice] = useState('');
  const [error,setError] = useState('');
  const [busy,setBusy] = useState(false);
  useEffect(()=>{api('/student-profile/').then(setProfile).catch(err=>setError(err.message));},[]);
  async function save(event) {
    event.preventDefault();setBusy(true);setError('');setNotice('');
    const form = new FormData();
    form.append('skills',profile.skills || '');
    form.append('github_url',profile.github_url || '');
    form.append('linkedin_url',profile.linkedin_url || '');
    if(resume) form.append('resume',resume);
    try {
      const updated = await api('/student-profile/',{method:'PATCH',body:form});
      setProfile(updated);setResume(null);setNotice('Your profile has been updated.');
    } catch(err){setError(err.message);}
    finally{setBusy(false);}
  }
  return <section className="panel section-gap"><div className="panel-heading"><div><h3>My professional profile</h3><p>Add skills and links so recruiters can learn more about you.</p></div><Tag tone={profile.resume_uploaded?'green':'amber'}>{profile.resume_uploaded?'Resume uploaded':'Resume missing'}</Tag></div>
    {error&&<div className="alert error">{error}</div>}{notice&&<div className="alert success">{notice}</div>}
    <form className="form-grid" onSubmit={save}>
      <label className="span-two">Skills (comma separated)<textarea rows="3" maxLength="2000" value={profile.skills} onChange={e=>setProfile({...profile,skills:e.target.value})} placeholder="Python, Django, REST APIs, SQL, C++"/></label>
      <label>GitHub profile<input type="url" value={profile.github_url} onChange={e=>setProfile({...profile,github_url:e.target.value})} placeholder="https://github.com/username"/></label>
      <label>LinkedIn profile<input type="url" value={profile.linkedin_url} onChange={e=>setProfile({...profile,linkedin_url:e.target.value})} placeholder="https://linkedin.com/in/username"/></label>
      <label className="span-two">Resume (PDF, maximum 5 MB)<input type="file" accept="application/pdf,.pdf" onChange={e=>setResume(e.target.files?.[0] || null)}/></label>
      <div className="profile-actions"><button className="btn primary" disabled={busy}>{busy?'Saving…':'Save profile'}</button>{profile.resume_uploaded&&<button type="button" className="btn" onClick={()=>downloadProtectedFile(`/students/${user.id}/resume/`,`${user.roll_number || user.username}_resume.pdf`).catch(err=>setError(err.message))}>Download my resume</button>}</div>
    </form>
  </section>;
}

function StudentDashboard() {
  const [drives, setDrives] = useState([]);
  const [applications, setApplications] = useState([]);
  const [profile, setProfile] = useState(null);
  const [error, setError] = useState('');
  async function load() {
    try { const [p,d,a] = await Promise.all([api('/student-zone/'),api('/drive/'),api('/application/')]); setProfile(p.profile); setDrives(safeList(d)); setApplications(safeList(a)); }
    catch (err) { setError(err.message); }
  }
  useEffect(() => { load(); }, []);
  async function apply(driveId) {
    try { await api('/application/', {method:'POST',body:JSON.stringify({drive:driveId})}); await load(); }
    catch (err) { setError(err.message); }
  }
  const applied = new Set(applications.map(a=>a.drive));
  return <><PageHeader eyebrow="STUDENT WORKSPACE" title={`Welcome, ${profile?.username || 'student'}`} subtitle="Explore verified opportunities and keep track of your applications." />
    {error && <div className="alert error">{error}</div>}
    <div className="stats-grid"><Stat label="Available drives" value={drives.length} note="Currently listed opportunities" /><Stat label="Applications" value={applications.length} note="Your submitted applications" /><Stat label="CGPA" value={profile?.cgpa} note="From the official roster" /></div>
    <section className="panel section-gap"><div className="panel-heading"><div><h3>Open placement drives</h3><p>Apply to opportunities that match your academic profile.</p></div></div>
      <DataTable columns={[{key:'company_name',label:'Company'},{key:'role_title',label:'Role'},{key:'package_lpa',label:'Package (LPA)'},{key:'min_cgpa',label:'Min CGPA'},{key:'application_deadline',label:'Deadline'},{key:'action',label:'Action',render:d=>applied.has(d.id)?<Tag tone="green">Applied</Tag>:<button className="btn small primary" onClick={()=>apply(d.id)}>Apply</button>}]} rows={drives} empty="No open drives are available right now." />
    </section>
    <section className="panel section-gap"><div className="panel-heading"><div><h3>My applications</h3><p>Track your placement progress.</p></div></div>
      <DataTable columns={[{key:'company_name',label:'Company'},{key:'role_title',label:'Role'},{key:'status',label:'Status',render:a=><Tag tone={a.status==='SELECTED'?'green':a.status==='REJECTED'?'red':'blue'}>{a.status}</Tag>},{key:'interview_at',label:'Interview',render:a=>a.interview_at?new Date(a.interview_at).toLocaleString():'—'},{key:'interview_mode',label:'Mode'},{key:'applied_at',label:'Applied on',render:a=>new Date(a.applied_at).toLocaleDateString()}]} rows={applications} />
    </section>
    <StudentProfilePanel />
  </>;
}

function RecruiterDashboard() {
  const [summary,setSummary] = useState(null);
  const [drives,setDrives] = useState([]);
  const [applications,setApplications] = useState([]);
  const [selectedIds,setSelectedIds] = useState([]);
  const [filters,setFilters] = useState({search:'',min_cgpa:'',max_backlogs:'',status:''});
  const [interviewAt,setInterviewAt] = useState('');
  const [interviewMode,setInterviewMode] = useState('ONLINE');
  const [form,setForm] = useState({role_title:'',description:'',location:'',package_lpa:'',min_cgpa:'6',max_backlogs:'0',application_deadline:''});
  const [error,setError] = useState('');
  const [notice,setNotice] = useState('');
  async function load() {
    try {
      const query = new URLSearchParams(Object.entries(filters).filter(([,value])=>value!=='')).toString();
      const [s,d,a] = await Promise.all([api('/recruiter-zone/'),api('/drive/'),api('/application/'+(query?'?'+query:''))]);
      setSummary(s);setDrives(safeList(d));setApplications(safeList(a));
      setSelectedIds(current=>current.filter(id=>safeList(a).some(item=>item.id===id)));
    } catch(err){setError(err.message);}
  }
  useEffect(()=>{load();},[filters]);
  async function createDrive(e){
    e.preventDefault();setError('');setNotice('');
    try { await api('/drive/',{method:'POST',body:JSON.stringify({...form,package_lpa:Number(form.package_lpa),min_cgpa:Number(form.min_cgpa),max_backlogs:Number(form.max_backlogs),is_active:true})});setNotice('Placement drive created.');setForm({role_title:'',description:'',location:'',package_lpa:'',min_cgpa:'6',max_backlogs:'0',application_deadline:''});await load();}
    catch(err){setError(err.message);}
  }
  async function updateStatus(id,statusValue,extra={}) {
    setError('');
    try{await api(`/application/${id}/`,{method:'PATCH',body:JSON.stringify({status:statusValue,...extra})});setNotice('Candidate status updated.');await load();}
    catch(err){setError(err.message);}
  }
  async function bulkUpdate(statusValue) {
    setError('');
    try {
      await api('/application/bulk-status/',{method:'POST',body:JSON.stringify({application_ids:selectedIds,status:statusValue})});
      setSelectedIds([]);setNotice(`Updated ${selectedIds.length} candidates.`);await load();
    } catch(err){setError(err.message);}
  }
  function toggleSelected(id) {
    setSelectedIds(current=>current.includes(id)?current.filter(value=>value!==id):[...current,id]);
  }
  const selectable = applications.filter(a=>['APPLIED','SHORTLISTED'].includes(a.status));
  return <><PageHeader eyebrow="RECRUITER WORKSPACE" title="Hiring dashboard" subtitle="Publish opportunities and manage candidates for your placement drives." />
    {error&&<div className="alert error">{error}</div>}{notice&&<div className="alert success">{notice}</div>}
    <div className="stats-grid"><Stat label="Approval status" value={summary?.approval_status} note="TPO verification" /><Stat label="Your drives" value={drives.length} note="Published opportunities" /><Stat label="Applicants" value={applications.length} note="Across filtered results" /></div>
    {summary?.approval_status !== 'APPROVED' ? <div className="panel section-gap"><h3>Account awaiting approval</h3><p className="muted">The TPO must approve your recruiter account before you can publish drives or review candidates.</p><Tag tone="amber">{summary?.approval_status || 'PENDING'}</Tag></div> : <>
      <div className="content-grid section-gap"><section className="panel"><div className="panel-heading"><div><h3>Create a placement drive</h3><p>Publish a role for eligible students.</p></div></div>
        <form className="form-grid" onSubmit={createDrive}>
          <label>Role title<input required value={form.role_title} onChange={e=>setForm({...form,role_title:e.target.value})}/></label>
          <label>Location<input value={form.location} onChange={e=>setForm({...form,location:e.target.value})}/></label>
          <label>Package (LPA)<input type="number" min="0" step="0.01" required value={form.package_lpa} onChange={e=>setForm({...form,package_lpa:e.target.value})}/></label>
          <label>Minimum CGPA<input type="number" min="0" max="10" step="0.01" value={form.min_cgpa} onChange={e=>setForm({...form,min_cgpa:e.target.value})}/></label>
          <label>Maximum backlogs<input type="number" min="0" value={form.max_backlogs} onChange={e=>setForm({...form,max_backlogs:e.target.value})}/></label>
          <label>Application deadline<input type="datetime-local" value={form.application_deadline} onChange={e=>setForm({...form,application_deadline:e.target.value})}/></label>
          <label className="span-two">Description<textarea rows="3" value={form.description} onChange={e=>setForm({...form,description:e.target.value})}/></label>
          <button className="btn primary">Publish drive →</button>
        </form>
      </section><section className="panel"><div className="panel-heading"><div><h3>Your active drives</h3><p>Roles posted by your company.</p></div></div>
        {drives.map(d=><div className="drive-row" key={d.id}><div><strong>{d.role_title}</strong><small>{d.location || 'Location not specified'} · {d.package_lpa} LPA</small></div><Tag tone={d.is_open?'green':'amber'}>{d.is_open?'Open':'Closed'}</Tag></div>)}
        {!drives.length&&<div className="empty compact">No drives posted yet.</div>}
      </section></div>
      <section className="panel section-gap"><div className="panel-heading"><div><h3>Candidate pipeline</h3><p>Filter candidates and update their recruitment stage.</p></div><Tag>{applications.length} results</Tag></div>
        <div className="filter-bar">
          <input aria-label="Search candidates" placeholder="Search name, roll number or role" value={filters.search} onChange={e=>setFilters({...filters,search:e.target.value})}/>
          <input aria-label="Minimum CGPA" type="number" min="0" max="10" step="0.1" placeholder="Min CGPA" value={filters.min_cgpa} onChange={e=>setFilters({...filters,min_cgpa:e.target.value})}/>
          <input aria-label="Maximum backlogs" type="number" min="0" placeholder="Max backlogs" value={filters.max_backlogs} onChange={e=>setFilters({...filters,max_backlogs:e.target.value})}/>
          <select aria-label="Filter by status" value={filters.status} onChange={e=>setFilters({...filters,status:e.target.value})}><option value="">All stages</option>{['APPLIED','SHORTLISTED','INTERVIEW','SELECTED','REJECTED'].map(s=><option key={s}>{s}</option>)}</select>
        </div>
        {selectedIds.length>0&&<div className="bulk-bar"><strong>{selectedIds.length} selected</strong><button className="btn small" onClick={()=>bulkUpdate('SHORTLISTED')}>Bulk shortlist</button><button className="btn small danger" onClick={()=>bulkUpdate('REJECTED')}>Bulk reject</button><button className="btn small text-btn" onClick={()=>setSelectedIds([])}>Clear</button></div>}
        <DataTable columns={[
          {key:'select',label:'',render:a=>selectable.some(x=>x.id===a.id)?<input aria-label={`Select ${a.student_roll_number}`} type="checkbox" checked={selectedIds.includes(a.id)} onChange={()=>toggleSelected(a.id)}/>:null},
          {key:'student_roll_number',label:'Roll number'},
          {key:'student_name',label:'Student'},
          {key:'role_title',label:'Role'},
          {key:'student_cgpa',label:'CGPA'},
          {key:'student_backlogs',label:'Backlogs'},{key:'student_profile',label:'Portfolio',render:a=><div className="portfolio-cell">{a.student_profile?.skills&&<small>{a.student_profile.skills.slice(0,55)}{a.student_profile.skills.length>55?'…':''}</small>}{a.student_profile?.github_url&&<a href={a.student_profile.github_url} target="_blank" rel="noreferrer">GitHub</a>}{a.student_profile?.linkedin_url&&<a href={a.student_profile.linkedin_url} target="_blank" rel="noreferrer">LinkedIn</a>}{a.student_profile?.resume_available&&<button className="btn small" onClick={()=>downloadProtectedFile(a.student_profile.resume_url,`${a.student_roll_number}_resume.pdf`).catch(err=>setError(err.message))}>Resume ↓</button>}</div>},
          {key:'status',label:'Current stage',render:a=><Tag>{a.status}</Tag>},
          {key:'interview_at',label:'Interview',render:a=>a.interview_at?new Date(a.interview_at).toLocaleString():'—'},
          {key:'actions',label:'Update',render:a=><div className="row-actions">
            {a.status==='APPLIED'&&<><button className="btn small" onClick={()=>updateStatus(a.id,'SHORTLISTED')}>Shortlist</button><button className="btn small danger" onClick={()=>updateStatus(a.id,'REJECTED')}>Reject</button></>}
            {a.status==='SHORTLISTED'&&<><button className="btn small primary" disabled={!interviewAt} onClick={()=>updateStatus(a.id,'INTERVIEW',{interview_at:new Date(interviewAt).toISOString(),interview_mode:interviewMode})}>Schedule interview</button><button className="btn small" onClick={()=>updateStatus(a.id,'SELECTED')}>Select</button><button className="btn small danger" onClick={()=>updateStatus(a.id,'REJECTED')}>Reject</button></>}
            {a.status==='INTERVIEW'&&<><button className="btn small primary" onClick={()=>updateStatus(a.id,'SELECTED')}>Select</button><button className="btn small danger" onClick={()=>updateStatus(a.id,'REJECTED')}>Reject</button></>}
            {['SELECTED','REJECTED'].includes(a.status)&&<Tag tone={a.status==='SELECTED'?'green':'red'}>{a.status}</Tag>}
          </div>}
        ]} rows={applications} />
        <div className="interview-tools"><label>Interview date & time<input type="datetime-local" value={interviewAt} onChange={e=>setInterviewAt(e.target.value)}/></label><label>Mode<select value={interviewMode} onChange={e=>setInterviewMode(e.target.value)}><option value="ONLINE">Online</option><option value="IN_PERSON">In person</option></select></label></div>
      </section>
    </>}
  </>;
}

function safeList(data) { return Array.isArray(data) ? data : data?.results || []; }

function Dashboard() {
  const { user } = useAuth();
  return <AppLayout>
    {user.role === 'TPO' ? <TpoDashboard /> : user.role === 'RECRUITER' ? <RecruiterDashboard /> : <StudentDashboard />}
  </AppLayout>;
}

function RootRedirect() {
  const { user, loading } = useAuth();
  if (loading) return <ScreenLoader />;
  return <Navigate to={user ? '/' : '/login'} replace />;
}

export default function App() {
  const { user } = useAuth();
  return <Routes>
    <Route path="/login" element={user ? <Navigate to="/" replace /> : <Login />} />
    <Route path="/register" element={user ? <Navigate to="/" replace /> : <Register />} />
    <Route path="/register/recruiter" element={user ? <Navigate to="/" replace /> : <RecruiterRegister />} />
    <Route path="/" element={<Protected><Dashboard /></Protected>} />
    <Route path="*" element={<RootRedirect />} />
  </Routes>;
}

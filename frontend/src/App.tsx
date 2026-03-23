import { Routes, Route, Navigate } from 'react-router-dom';
import { useState, useEffect, createContext, useContext } from 'react';
import axios from 'axios';
const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';
interface AuthCtx { user: any; isAuth: boolean; loading: boolean; login: (e: string, p: string) => Promise<void>; logout: () => void; }
const AuthContext = createContext<AuthCtx>({} as AuthCtx);
function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<any>(null); const [loading, setLoading] = useState(true);
  useEffect(() => { const t = localStorage.getItem('sv_token'); if (t) setUser({ id: localStorage.getItem('sv_uid') }); setLoading(false); }, []);
  const login = async (e: string, p: string) => { const r = await axios.post(`${API}/api/auth/login`, { email: e, password: p }); localStorage.setItem('sv_token', r.data.access_token); localStorage.setItem('sv_uid', r.data.user_id); setUser({ id: r.data.user_id }); };
  const logout = () => { localStorage.clear(); setUser(null); };
  return <AuthContext.Provider value={{ user, isAuth: !!user, loading, login, logout }}>{children}</AuthContext.Provider>;
}
const useAuth = () => useContext(AuthContext);
const client = axios.create({ baseURL: API }); client.interceptors.request.use(c => { const t = localStorage.getItem('sv_token'); if (t) c.headers.Authorization = `Bearer ${t}`; return c; });

function Layout() {
  const { logout } = useAuth();
  const nav = [{ to: '/', l: 'Home' }, { to: '/trending', l: 'Trending' }, { to: '/subscriptions', l: 'Subscriptions' }, { to: '/library', l: 'Library' }, { to: '/upload', l: 'Upload' }, { to: '/channel', l: 'My Channel' }, { to: '/history', l: 'History' }, { to: '/playlists', l: 'Playlists' }];
  return (<div className="flex h-screen bg-gray-50 dark:bg-gray-900"><aside className="w-56 bg-white dark:bg-gray-800 border-r p-4 hidden md:block"><h1 className="text-xl font-bold text-red-600 mb-6">Video Platform</h1><nav className="space-y-1">{nav.map(n => <a key={n.to} href={n.to} className="block px-3 py-2 rounded text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700">{n.l}</a>)}</nav><button onClick={logout} className="mt-8 text-sm text-gray-400">Logout</button></aside><main className="flex-1 overflow-y-auto p-6">
    <Routes>
      <Route index element={<VideoGrid title="Home" endpoint="/api/feed" />} />
      <Route path="trending" element={<VideoGrid title="Trending" endpoint="/api/feed/trending" />} />
      <Route path="subscriptions" element={<VideoGrid title="Subscriptions" endpoint="/api/feed/subscriptions" />} />
      <Route path="library" element={<VideoGrid title="Library" endpoint="/api/playlists" />} />
      <Route path="history" element={<VideoGrid title="Watch History" endpoint="/api/history" />} />
      <Route path="playlists" element={<VideoGrid title="Playlists" endpoint="/api/playlists" />} />
      <Route path="upload" element={<div><h1 className="text-2xl font-bold mb-6 dark:text-white">Upload Video</h1><div className="bg-white dark:bg-gray-800 rounded-lg p-8 border text-center"><p className="text-gray-500">Drag and drop a video file or click to upload</p></div></div>} />
      <Route path="channel" element={<div><h1 className="text-2xl font-bold dark:text-white">My Channel</h1></div>} />
      <Route path="video/:id" element={<div><h1 className="text-2xl font-bold dark:text-white">Video Player</h1></div>} />
    </Routes>
  </main></div>);
}

function VideoGrid({ title, endpoint }: { title: string; endpoint: string }) {
  const [videos, setVideos] = useState<any[]>([]); const [loading, setLoading] = useState(true);
  useEffect(() => { client.get(endpoint).then(r => setVideos(Array.isArray(r.data) ? r.data : r.data.items || [])).catch(() => {}).finally(() => setLoading(false)); }, [endpoint]);
  return (<div><h1 className="text-2xl font-bold mb-6 dark:text-white">{title}</h1>{loading ? <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">{[1,2,3,4,5,6,7,8].map(i => <div key={i} className="animate-pulse"><div className="h-40 bg-gray-200 dark:bg-gray-700 rounded-lg" /><div className="h-4 bg-gray-200 dark:bg-gray-700 rounded mt-2 w-3/4" /></div>)}</div> :
    <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">{videos.map((v: any, i) => <a key={v.id || i} href={`/video/${v.id}`} className="block group"><div className="relative"><img src={v.thumbnail_url || 'https://via.placeholder.com/320x180'} alt={v.title} className="w-full h-40 object-cover rounded-lg" />{v.duration && <span className="absolute bottom-1 right-1 bg-black/80 text-white text-xs px-1 rounded">{Math.floor(v.duration/60)}:{(v.duration%60).toString().padStart(2,'0')}</span>}</div><h3 className="text-sm font-medium mt-2 dark:text-white group-hover:text-red-600">{v.title}</h3><p className="text-xs text-gray-500">{v.channel_name || 'Channel'} - {v.view_count || 0} views</p></a>)}</div>}
  </div>);
}

function Login() {
  const [email, setEmail] = useState(''); const [pw, setPw] = useState(''); const [err, setErr] = useState(''); const { login } = useAuth();
  return (<div className="min-h-screen flex items-center justify-center bg-gray-900"><div className="bg-white rounded-xl p-8 w-96 shadow-xl"><h1 className="text-2xl font-bold text-center text-red-600 mb-6">Video Platform</h1>{err && <p className="text-red-500 text-sm mb-4">{err}</p>}<form onSubmit={async e => { e.preventDefault(); try { await login(email, pw); window.location.href = '/'; } catch { setErr('Invalid'); } }} className="space-y-4"><input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="Email" className="w-full px-3 py-2 border rounded-lg" /><input type="password" value={pw} onChange={e => setPw(e.target.value)} placeholder="Password" className="w-full px-3 py-2 border rounded-lg" /><button className="w-full bg-red-600 text-white py-2 rounded-lg">Sign In</button></form></div></div>);
}

export default function App() {
  return (<AuthProvider><Routes><Route path="/login" element={<Login />} /><Route path="/*" element={(() => { const { isAuth, loading } = useAuth(); if (loading) return <div>Loading...</div>; return isAuth ? <Layout /> : <Navigate to="/login" />; })()} /></Routes></AuthProvider>);
}

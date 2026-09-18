
import { useState, useEffect } from "react"

export default function SpectreUI() {
  const [objective, setObjective] = useState("")
  const [registry, setRegistry] = useState({})
  const [mission, setMission] = useState(null)
  const [loading, setLoading] = useState(false)
  const [trace, setTrace] = useState([])

  useEffect(()=>{ fetch("http://localhost:8000/registry").then(r=>r.json()).then(setRegistry).catch(()=>{}) },[])

  const runMission = async () => {
    if(!objective) return
    setLoading(true)
    setTrace([{phase:"INIT", msg:`Objective: ${objective}`}])
    try {
      const res = await fetch("http://localhost:8000/mission", {
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body: JSON.stringify({objective, allow_paid:false})
      })
      const data = await res.json()
      setMission(data)
      setTrace(data.trace || [])
    } catch(e) {
      setTrace(prev=>[...prev, {phase:"ERROR", msg:String(e)}])
    }
    setLoading(false)
  }

  return (
    <div style={{background:"#0a0a0a", color:"#e5e5e5", minHeight:"100vh", fontFamily:"monospace", padding:24}}>
      <h1 style={{fontSize:32, letterSpacing:2}}>SPECTRE // MASTER AGENT</h1>
      <p style={{color:"#888"}}>UNDERSTAND → RESEARCH → PLAN → DISCOVER → SELECT → EXECUTE → OBSERVE → VALIDATE → REPAIR → DELIVER</p>

      <div style={{display:"grid", gridTemplateColumns:"1fr 320px", gap:24, marginTop:24}}>
        <div>
          <div style={{background:"#111", border:"1px solid #222", padding:16, borderRadius:12}}>
            <label style={{display:"block", marginBottom:8, color:"#aaa"}}>NATURAL LANGUAGE OBJECTIVE</label>
            <textarea value={objective} onChange={e=>setObjective(e.target.value)} placeholder="e.g., Build a python script that scrapes HN top stories and saves to CSV with validation" style={{width:"100%", height:120, background:"#0a0a0a", color:"#fff", border:"1px solid #333", padding:12, borderRadius:8}} />
            <button onClick={runMission} disabled={loading} style={{marginTop:12, background:"#fff", color:"#000", padding:"10px 20px", borderRadius:8, fontWeight:"bold", cursor:"pointer"}}>{loading?"ORCHESTRATING...":"EXECUTE MISSION"}</button>
          </div>

          <div style={{marginTop:24, background:"#111", border:"1px solid #222", padding:16, borderRadius:12}}>
            <h3>Live Trace</h3>
            <div style={{maxHeight:400, overflowY:"auto", fontSize:12}}>
              {trace.map((t,i)=><div key={i} style={{padding:"4px 0", borderBottom:"1px solid #1a1a1a"}}><span style={{color:"#666"}}>[{t.phase}]</span> {t.msg}</div>)}
            </div>
          </div>

          {mission && (
            <div style={{marginTop:24, background:"#111", border:"1px solid #222", padding:16, borderRadius:12}}>
              <h3>Mission {mission.mission_id} - {mission.status}</h3>
              <pre style={{whiteSpace:"pre-wrap", fontSize:12, color:"#ccc"}}>{JSON.stringify(mission.final_output, null, 2)}</pre>
            </div>
          )}
        </div>

        <div>
          <div style={{background:"#111", border:"1px solid #222", padding:16, borderRadius:12}}>
            <h3 style={{marginTop:0}}>Agent Registry ({Object.keys(registry).length})</h3>
            <div style={{fontSize:11, color:"#888", marginBottom:12}}>Routing: local_free → oss_hosted → free_tier → paid</div>
            {Object.entries(registry).map(([id, spec])=><div key={id} style={{padding:8, background:"#0a0a0a", borderRadius:6, marginBottom:8, border:"1px solid #222"}}>
              <div style={{fontWeight:"bold"}}>{spec.name}</div>
              <div style={{color:"#666"}}>{id} • {spec.tier} • {spec.status}</div>
              <div style={{color:"#888", fontSize:10}}>{spec.capabilities?.join(", ")}</div>
            </div>)}
          </div>
        </div>
      </div>
    </div>
  )
}

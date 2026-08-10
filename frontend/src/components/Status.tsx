export function Status({kind,label}:{kind:'confirmed'|'review'|'invalid';label:string}){return <span className={`status ${kind}`}><i aria-hidden="true"/> {label}</span>}

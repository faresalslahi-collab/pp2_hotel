function e(t,r){const n=new Intl.NumberFormat("en-US",{minimumFractionDigits:0,maximumFractionDigits:2}).format(t);return`${r} ${n}`}function m(t){if(!t)return"—";const r=new Date(t);return Number.isNaN(r.getTime())?t:new Intl.DateTimeFormat("en-US",{month:"short",day:"numeric",year:"numeric"}).format(r)}export{e as a,m as f};
//# sourceMappingURL=format-BYDFEyXj.js.map

function e(t){const a=t.getFullYear(),n=String(t.getMonth()+1).padStart(2,"0"),o=String(t.getDate()).padStart(2,"0");return`${a}-${n}-${o}`}function r(){return e(new Date)}function s(t,a){const n=new Date(`${t}T00:00:00`);return n.setDate(n.getDate()+a),e(n)}export{s as a,r as t};
//# sourceMappingURL=dates-ev-JZFQP.js.map

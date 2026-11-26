// Prints a compact summary of an exported DlgSystem .dlg.json file.
const fs = require("fs");
const d = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const cond = (c) => {
  const v = c.ConditionType.includes("Int") ? c.Operation.split("::")[1] +
    c.IntValue : c.ConditionType.includes("Name") ? (c.bBoolValue ? "=" :
    "!=") + c.NameValue : c.ConditionType.includes("Bool") ? "=" +
    c.bBoolValue : "";
  return c.ConditionType.split("::")[1] + ":" + c.CallbackName + v;
};
const ev = (e) => e.EventType.split("::")[1] + ":" + e.EventName +
  (e.EventType.includes("Name") ? "=" + e.NameValue : "") +
  (e.EventType.includes("Int") ? (e.bDelta ? "+" : "=") + e.IntValue : "") +
  (e.EventType.includes("Bool") ? "=" + e.bValue : "");
const edges = (n) => n.Children.map((c) => "    -> " + c.TargetIndex +
  (c.Text ? ' "' + c.Text + '"' : "") + (c.Conditions.length ? " [" +
  c.Conditions.map(cond).join(", ") + "]" : "")).join("\n");
console.log("START\n" + d.StartNodes.map(edges).join("\n"));
for (const n of d.Nodes) {
  console.log(n.__index__ + " " + n.__type__.replace("DlgNode_", "") +
    (n.Text ? ' "' + n.Text + '"' : "") + (n.EnterEvents.length ? " {" +
    n.EnterEvents.map(ev).join(", ") + "}" : ""));
  if (n.Children.length) console.log(edges(n));
}

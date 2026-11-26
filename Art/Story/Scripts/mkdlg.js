// Builds a DlgSystem .dlg.json from a compact spec (see dlg_fencehole.js).
// Workflow (story-system.md, Dialogs from scripts): Acrpg.DlgExport the
// dialogue, run this over the exported file, Acrpg.DlgImport, save, delete
// the .dlg.json.
// Usage: node mkdlg.js <spec.js> <exported.dlg.json to overwrite>
const fs = require("fs");
const crypto = require("crypto");
const spec = require(require("path").resolve(process.argv[2]));
const out = process.argv[3];
const base = JSON.parse(fs.readFileSync(out, "utf8"));
const guid = () => crypto.randomBytes(16).toString("hex").toUpperCase();
const owner = spec.owner;
const cond = ([kind, id, op, value]) => {
  const c = { Strength: "EDlgConditionStrength::Strong",
    ConditionType: "EDlgConditionType::" + kind, ParticipantName: "Story",
    CallbackName: id, Operation: "EDlgOperation::Equal",
    CompareType: "EDlgCompare::ToConst", OtherParticipantName: "None",
    OtherVariableName: "None", IntValue: 0, FloatValue: 0,
    NameValue: "None", bBoolValue: true, bLongTermMemory: true,
    GUID: "00000000000000000000000000000000", CustomCondition: null };
  if (kind === "NameCall") { c.NameValue = value; c.bBoolValue = op === "=="; }
  if (kind === "IntCall") { c.Operation = "EDlgOperation::" + op;
    c.IntValue = value; }
  if (kind === "BoolCall") c.bBoolValue = value;
  return c;
};
const ev = ([kind, id, value]) => ({ ParticipantName: "Story",
  EventType: "EDlgEventType::" + kind, EventName: id,
  IntValue: kind === "ModifyInt" ? value : 0, FloatValue: 0,
  NameValue: kind === "ModifyName" ? value : "None",
  bDelta: kind === "ModifyInt", bValue: kind === "ModifyBool" ? value : false,
  CustomEvent: null });
const edge = ([target, text, conds]) => ({ TargetIndex: target,
  Conditions: (conds || []).map(cond), SpeakerState: "None",
  bIncludeInAllOptionListIfUnsatisfied: true, EdgeData: null,
  Text: text || "", TextArguments: [] });
const common = (n) => ({ OwnerName: owner,
  bCheckChildrenOnEvaluation: n.type === "Selector",
  EnterConditions: [], EnterRestriction: "EDlgEntryRestriction::None",
  EnterEvents: (n.events || []).map(ev), NodeGUID: guid(),
  Children: (n.edges || []).map(edge) });
const nodes = spec.nodes.map((n, i) => {
  const head = { __index__: i, __type__: "DlgNode_" + n.type };
  if (n.type === "Speech") Object.assign(head, { bIsVirtualParent: false,
    bVirtualParentFireDirectChildEnterEvents: true, Text: n.text,
    TextArguments: [], SpeakerState: "None", NodeData: null,
    VoiceSoundWave: "", VoiceDialogueWave: "", GenericData: "" });
  if (n.type === "Selector") Object.assign(head, {
    SelectorType: "EDlgNodeSelectorType::First",
    bAvoidPickingSameOptionTwiceInARow: false,
    bCycleThroughSatisfiedOptionsWithoutRepetition: false });
  return Object.assign(head, common(n));
});
base.ParticipantsClasses = [{ ParticipantName: owner, ParticipantClass: "" },
  { ParticipantName: "Story",
    ParticipantClass: "/Script/acrpg.StoryStateSubsystem" }];
base.StartNodes = [Object.assign({ __type__: "DlgNode_Start" },
  common({ edges: spec.start }))];
base.Nodes = nodes;
base.NodesGUIDToIndexMap = Object.fromEntries(
  nodes.map((n, i) => [n.NodeGUID, i]));
fs.writeFileSync(out, JSON.stringify(base, null, "\t"));
console.log("wrote " + nodes.length + " nodes to " + out);

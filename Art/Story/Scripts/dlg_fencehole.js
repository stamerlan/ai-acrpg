// The fence hole dialog (DLG_FenceHole): node mkdlg.js dlg_fencehole.js
// Content/Story/Stop0/Dialogs/DLG_FenceHole.dlg.json
// Edges are listed right to left: the importer's auto layout reverses them
const look = "*A hole in the fence, half hidden behind the gnome crates. " +
  "The impound lot is right behind it.*";
module.exports = {
  owner: "FenceHole",
  start: [[0]],
  nodes: [
    { type: "Selector", edges: [
      [2, "", [["NameCall", "q_car_trouble", "!=", "office"]]],
      [1, "", [["NameCall", "q_car_trouble", "==", "office"]]]] },
    { type: "Speech", text: look, edges: [
      [4, "Not yet."],
      [3, "Too bright. They'd see me. I'll wait until midnight."]] },
    { type: "Speech", text: look, edges: [
      [4, "Too bright. They'd see me."]] },
    { type: "End", events: [["Event", "wait_for_midnight"]] },
    { type: "End" },
  ],
};

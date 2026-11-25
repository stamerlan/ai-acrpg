// Turns reference images into textured models with Meshy image-to-3D.
// Usage: MKEY=<key> node meshy.js <name>:<polycount> ...
// Reads Models/Reference/<name>.jpg, writes Models/<name>.glb. Task ids
// are kept in Models/tasks.json, so a rerun resumes instead of paying
// for the same model twice.
const fs = require("fs");
const path = require("path");

const models = path.join(__dirname, "..", "Models");
const tasksPath = path.join(models, "tasks.json");
const tasks = fs.existsSync(tasksPath)
  ? JSON.parse(fs.readFileSync(tasksPath, "utf8")) : {};
const api = "https://api.meshy.ai/openapi/v1/image-to-3d";
const headers = { Authorization: "Bearer " + process.env.MKEY,
  "Content-Type": "application/json" };

async function call(url, options) {
  for (let attempt = 0; ; attempt += 1) {
    try {
      return await (await fetch(url, options)).json();
    } catch (error) {
      if (attempt === 4) throw error;
      await new Promise((resolve) => setTimeout(resolve, 5000));
    }
  }
}

async function run(job) {
  const [name, polycount] = job.split(":");
  if (!tasks[name]) {
    const image = fs.readFileSync(
      path.join(models, "Reference", name + ".jpg")).toString("base64");
    const reply = await call(api, { method: "POST", headers,
      body: JSON.stringify({
        image_url: "data:image/jpeg;base64," + image,
        ai_model: "meshy-t2.5", model_type: "smart-topology",
        target_polycount: Number(polycount),
        should_texture: true }) });
    if (!reply.result) {
      console.log(name, "REFUSED", JSON.stringify(reply));
      return;
    }
    tasks[name] = reply.result;
    fs.writeFileSync(tasksPath, JSON.stringify(tasks, null, 1));
  }
  for (;;) {
    const reply = await call(api + "/" + tasks[name], { headers });
    if (reply.status === "SUCCEEDED") {
      const file = await fetch(reply.model_urls.glb);
      fs.writeFileSync(path.join(models, name + ".glb"),
        Buffer.from(await file.arrayBuffer()));
      console.log(name, "DONE");
      return;
    }
    if (["FAILED", "CANCELED", "EXPIRED"].includes(reply.status)) {
      console.log(name, reply.status, JSON.stringify(reply.task_error));
      return;
    }
    await new Promise((resolve) => setTimeout(resolve, 15000));
  }
}

(async () => {
  const jobs = [];
  for (const job of process.argv.slice(2)) {
    jobs.push(run(job).catch((error) => console.log(job, String(error))));
    await new Promise((resolve) => setTimeout(resolve, 4000));
  }
  await Promise.all(jobs);
})();

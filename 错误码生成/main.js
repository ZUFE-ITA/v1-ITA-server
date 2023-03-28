const fs = require("fs");
const path = require("path");

function gen_code(raw) {
	const map = {};
	for (const code in raw) {
		const msg = raw[code];
		let [_, dtype, name] = msg.toUpperCase().split(".");
		if (map[dtype] === undefined) {
			map[dtype] = [{ name, code }];
		} else {
			map[dtype].push({ name, code });
		}
	}

	function gen_block(clsName, kvs) {
		let head = `class ${clsName}:`;
		let body = kvs.map((d) => `    ${d.name} = ${d.code}`).join("\n");
		return `${head}\n${body}`;
	}

	let blocks = [];
	let error_code_map = [];
	for (const cls in map) {
		error_code_map.push({ name: cls, code: cls });
		blocks.push(gen_block(cls, map[cls]));
	}
	blocks.push(gen_block("ErrorCode", error_code_map));
	return blocks.join("\n\n");
}

const target = "./status-code.ts";
const raw = fs.readFileSync(path.resolve(__dirname, target), {
	encoding: "utf-8",
});
const dict = /(\{[^\}]+\})/i.exec(raw)[0];
const code = gen_code(eval(`(${dict})`));
fs.writeFileSync("./app/exceptions/error_code.py", code);

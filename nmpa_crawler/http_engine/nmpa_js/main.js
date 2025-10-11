// 占位 main.js：请将你在网页中扣下的 sign 生成逻辑粘贴进来，并在末尾输出 JSON
// 例如结合 md5(JSON.stringify(sorted_params)) 与时间戳生成。
// 运行: node main.js '{"url":"...","params":{...}}'

const fs = require('fs');

function echoSign(input) {
  // TODO: 替换为真实算法
  const data = JSON.parse(input || '{}');
  const ts = Date.now();
  // 非真实：仅返回时间戳与伪签名（请用真实算法替换）
  const sign = Buffer.from(JSON.stringify(data)).toString('base64').slice(0, 32);
  return { sign, timestamp: ts };
}

if (require.main === module) {
  const input = process.argv[2] || '{}';
  const result = echoSign(input);
  console.log(JSON.stringify(result));
}

module.exports = { echoSign };

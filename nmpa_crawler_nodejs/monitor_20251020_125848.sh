#!/bin/bash
echo "📊 NMPA 爬虫监控 - 20251020_125848"
echo "==============================="
echo "进程状态:"
ps -p 3700429 -o pid,etime,pcpu,pmem,cmd 2>/dev/null || echo "进程已结束"
echo ""
RUNS_BASE="outputs/runs"
LATEST_RUN=/tmp
if [ -z "" ]; then
    echo "输出目录: 暂无运行记录"
else
    echo "最新输出目录: "
    echo ""
    echo "输出文件大小:"
    ls -lh ""/datasets/*.jsonl 2>/dev/null | awk '{print $9 "\: " $5}' || echo "暂无数据文件"
fi
echo ""
echo "最近日志:"
tail -5 "crawler_20251020_125848.log" 2>/dev/null || echo "日志文件不存在"
echo ""
echo "实时监控命令: tail -f crawler_20251020_125848.log"

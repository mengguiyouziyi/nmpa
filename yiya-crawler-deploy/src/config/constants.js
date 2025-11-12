export const SITE_CONFIG = {
    nmpa: {
        code: "LG0001",
        domain: "www.nmpa.gov.cn",
        secondaryDomain: "nmpa.gov.cn",
        name: "国家药品监督管理局",
        pageList: [
            // 药品
            "https://www.nmpa.gov.cn/yaopin/ypjgdt/index.html", // 监管工作
            "https://www.nmpa.gov.cn/yaopin/ypggtg/index.html", // 公告通知
            "https://www.nmpa.gov.cn/yaopin/ypfgwj/index.html",// 法规文件
            "https://www.nmpa.gov.cn/yaopin/ypzhcjd/index.html", // 政策解读
            "https://www.nmpa.gov.cn/xxgk/kpzhsh/kpzhshyp/index.html", // 药品科普
            // 政策服务 - 政务服务门户首页 
            "https://www.nmpa.gov.cn/zwfw/zwfwgggs/index.html",
            "https://www.nmpa.gov.cn/zwfw/zwfwjfxx/index.html",
            "https://www.nmpa.gov.cn/zwfw/zwfwpjfbzs/index.html",
            "https://www.nmpa.gov.cn/zwfw/pjyjzs/index.html",
            "https://www.nmpa.gov.cn/zwfw/zwfwzxfw/zxfwbstj/index.html",
            "https://www.nmpa.gov.cn/zwfw/zwfwzxfw/zxfwfwpj/index.html",
            "https://www.nmpa.gov.cn/zwfw/zwfwzxfw/zxfwsjxz/index.html",
            // 政策服务 - 政策资讯
            "https://www.nmpa.gov.cn/xxgk/zhcjd/index.html", // 政策解读： 图、视频
            // 网站首页
            "https://www.nmpa.gov.cn/xxgk/zhqyj/index.html" //  征求意见
        ],
        oneTimePageList: [
            // 政策服务 - 热点服务
            "https://zwfw.nmpa.gov.cn/web/index/hotserver",// 热点服务
        ]
    },
    nifdc: {
        code: "LG0002",
        domain: "www.nifdc.org.cn",
        name: "中国食品药品检定研究院",
        pageList: [
            // 政策服务 - 公告通知
            "https://www.nifdc.org.cn/nifdc/xxgk/ggtzh/index.html",
            "https://www.nifdc.org.cn/nifdc/xxgk/zcfg/flfg/index.html", // 法规文件
            "https://www.nifdc.org.cn/nifdc/xxgk/zcfg/zcjd/index.html", // 法规政策 - 政策解读 
            "https://www.nifdc.org.cn/nifdc/xxgk/ggtzh/index.html", // 公告通知
            "https://www.nifdc.org.cn/nifdc/bshff/hzhpbzh/hzhpbzhtzgg/index.html", //化妆品标准
            "https://www.nifdc.org.cn/nifdc/bshff/xzq/index.html", // 下载区

            // ----- 办事大厅 // ----- 
            "https://www.nifdc.org.cn/nifdc/bshff/gjchj/index.html", //国家抽检

            // 医疗器械标准与分类管理
            "https://www.nifdc.org.cn/nifdc/bshff/ylqxbzhgl/index.html", // default
            "https://www.nifdc.org.cn/nifdc/bshff/ylqxbzhgl/qxgzzch/index.html", // 工作之窗
            "https://www.nifdc.org.cn/nifdc/bshff/ylqxbzhgl/qxggtzh/index.html", // 公告通知
            "https://www.nifdc.org.cn/nifdc/bshff/ylqxbzhgl/qxzqyj/index.html", // 征求意见
            "https://www.nifdc.org.cn/nifdc/bshff/ylqxbzhgl/qxxxgk/index.html", // 信息公开
            "https://www.nifdc.org.cn/nifdc/bshff/ylqxbzhgl/qxfgwj/index.html",//法规文件
            "https://www.nifdc.org.cn/nifdc/bshff/ylqxbzhgl/qxbzhjdxgpx/index.html",//标准解读与宣贯培训

            // 国家标准物质与菌毒种
            "https://www.nifdc.org.cn/nifdc/bshff/bzhwzh/bzwztzgg/index.html",

            // 检验业务 
            "https://www.nifdc.org.cn/nifdc/ywzx/jyywzx/cjgxwtjd/index.html", //检验业务咨询 - 常见共性问题解答
            "https://www.nifdc.org.cn/nifdc/bshff/jyyw/jyzzh/index.html", // 中检院检验资质
            "https://www.nifdc.org.cn/nifdc/bshff/jyyw/sjxzh/index.html", // 送检须知

            // 生物制品签发
            "https://bio.nifdc.org.cn/pqf/search.do?formAction=pqfGgtz",//生物制品批签发公告通知
            "https://bio.nifdc.org.cn/pqf/search.do?formAction=pqfJgtz", //生物制品批签发机构及调整
            "https://bio.nifdc.org.cn/pqf/search.do?formAction=pqfCyl", //生物制品批签发品种及抽样量
        ],
        oneTimePageList: [
            "http://app.nifdc.org.cn/jianybz/jybzTwoGj.do?formAction=listTsDalid&type=ybc&page=list_ybc",
            "https://www.nifdc.org.cn/nifdc/bshff/jyyw/jygzlch/index.html",
            "https://www.nifdc.org.cn/nifdc/ywzx/jyywzx/lxdh/index.html", // 检验工作流程
            "https://www.nifdc.org.cn/nifdc/bshff/jyyw/jyjcshx/index.html", // 检验检测时限
        ]
    },
    standalone: [
        "https://www.nmpa.gov.cn/xxgk/ggtg/ypggtg/ypshmshxdgg/20250516090939169.html"
    ]
};

export const SPIDER_SITE_TYPE = {
    page: "PAGE",
    file: "FILE"
};
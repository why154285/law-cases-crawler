// 1. 引入 Supabase 客户端（Node.js 版本）
import { createClient } from '@supabase/supabase-js';

// 2. 初始化 Supabase 连接（从 Vercel 环境变量读取配置）
const supabaseUrl = process.env.SUPABASE_URL || '';
const supabaseKey = process.env.SUPABASE_KEY || '';

// 安全校验：避免空值导致连接失败
if (!supabaseUrl || !supabaseKey) {
  console.error('Supabase 配置缺失：请在 Vercel 中配置 SUPABASE_URL 和 SUPABASE_KEY');
}

const supabase = createClient(supabaseUrl, supabaseKey);

// 3. 核心 API 处理函数（Vercel Serverless 入口）
export default async function handler(req, res) {
  // 允许跨域访问（EdgeOne Pages 调用必备）
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('Content-Type', 'application/json');

  // 处理 OPTIONS 预检请求（前端跨域必备）
  if (req.method === 'OPTIONS') {
    res.status(200).end();
    return;
  }

  // 仅处理 GET 请求
  if (req.method !== 'GET') {
    return res.status(405).json({
      code: 405,
      msg: '仅支持 GET 请求'
    });
  }

  try {
    // 4. 获取前端请求参数（分页/筛选）
    const page = parseInt(req.query.page || 1); // 默认第1页
    const size = parseInt(req.query.size || 10); // 默认每页10条
    const caseType = req.query.type || ''; // 案例类型筛选（可选）
    const offset = (page - 1) * size; // 分页偏移量

    // 5. 构建 Supabase 查询（支持筛选+排序+分页）
    let query = supabase.from('law_cases').select('*', { count: 'exact' });

    // 类型筛选（如果前端传了 type 参数）
    if (caseType) {
      query = query.eq('case_type', caseType);
    }

    // 按爬取时间降序排序（最新的在前）
    query = query.order('crawl_time', { ascending: false });

    // 分页（PostgreSQL 范围查询）
    query = query.range(offset, offset + size - 1);

    // 6. 执行查询
    const { data, count, error } = await query;

    // 处理 Supabase 错误
    if (error) {
      throw new Error(`Supabase 查询失败：${error.message}`);
    }

    // 7. 返回标准化响应（给 EdgeOne Pages 调用）
    return res.status(200).json({
      code: 200,
      msg: 'success',
      data: {
        list: data || [], // 案例列表（空数组兜底）
        pagination: {
          page: page,
          size: size,
          total: count || 0, // 总条数
          pages: count ? Math.ceil(count / size) : 0 // 总页数
        }
      }
    });

  } catch (err) {
    // 8. 全局错误处理（避免 API 崩溃）
    console.error('API 执行错误：', err);
    return res.status(500).json({
      code: 500,
      msg: `服务器内部错误：${err.message}`,
      data: null
    });
  }
}

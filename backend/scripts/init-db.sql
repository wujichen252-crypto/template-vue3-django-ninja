-- PostgreSQL 初始化配置
-- 创建数据库扩展和优化设置

-- 启用 UUID 扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 启用 pg_stat_statements 扩展（用于性能监控）
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- 设置默认参数（针对 Web 应用优化）
ALTER SYSTEM SET log_min_duration_statement = 1000; -- 记录超过 1 秒的慢查询
ALTER SYSTEM SET log_lock_waits = on; -- 记录锁等待
ALTER SYSTEM SET log_temp_files = 0; -- 记录所有临时文件使用
ALTER SYSTEM SET log_autovacuum_min_duration = 0; -- 记录所有 autovacuum 操作
ALTER SYSTEM SET track_activities = on;
ALTER SYSTEM SET track_counts = on;
ALTER SYSTEM SET track_io_timing = on;

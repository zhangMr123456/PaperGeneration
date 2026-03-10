-- 创建 document_context 表
CREATE TABLE document_context (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',

    -- DocumentMetadata 字段
    subject VARCHAR(20) NOT NULL DEFAULT '其他' COMMENT '科目: 语文,数学,英语,物理,化学,生物,历史,地理,政治,信息技术,通用技术,其他',
    grade VARCHAR(20) NOT NULL DEFAULT '其他' COMMENT '年级: 小学一年级到大学四年级,其他',
    doc_type VARCHAR(20) NOT NULL DEFAULT 'other' COMMENT '文档类型: textbook,examination_paper,text_material,other',
    confidence VARCHAR(10) NOT NULL DEFAULT 'low' COMMENT '置信度: high,medium,low',
    evidence VARCHAR(50) NOT NULL DEFAULT '' COMMENT '判断证据',

    -- DocumentContext 新增字段
    pdf_path VARCHAR(1000) NOT NULL DEFAULT '' COMMENT 'PDF文件路径',
    md_path VARCHAR(1000) NOT NULL DEFAULT '' COMMENT 'Markdown文件路径',
    stage VARCHAR(100) NOT NULL DEFAULT '' COMMENT '处理阶段',

    -- 时间戳字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',

    -- 索引（优化查询性能）
    INDEX idx_subject_grade (subject, grade),
    INDEX idx_doc_type (doc_type),
    INDEX idx_confidence (confidence),
    INDEX idx_created_at (created_at),
    INDEX idx_updated_at (updated_at),
    INDEX idx_paths (pdf_path(200), md_path(200))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='文档上下文表'
  ROW_FORMAT=DYNAMIC;

-- 创建 outline 表（支持层级结构，无外键约束）
CREATE TABLE outline (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY COMMENT '大纲ID',
    document_context_id BIGINT UNSIGNED NOT NULL COMMENT '关联的文档上下文ID',

    -- 大纲内容字段
    title VARCHAR(500) NOT NULL DEFAULT '' COMMENT '大纲标题',
    page_index INT NOT NULL DEFAULT 0 COMMENT '开始页码',
    begin_line_index INT NOT NULL DEFAULT 0 COMMENT '开始行索引',
    end_line_index INT NOT NULL DEFAULT 0 COMMENT '结束行索引',

    -- 层级结构字段
    parent_id BIGINT UNSIGNED DEFAULT NULL COMMENT '父级大纲ID',
    level SMALLINT UNSIGNED NOT NULL DEFAULT 1 COMMENT '层级深度',
    sort_order INT NOT NULL DEFAULT 0 COMMENT '排序顺序',

    -- 路径字段（优化树形查询）
    path VARCHAR(2000) NOT NULL DEFAULT '' COMMENT '层级路径',

    -- 时间戳字段
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '更新时间',

    -- 索引（优化层级查询性能）
    INDEX idx_document_context (document_context_id),
    INDEX idx_parent (parent_id),
    INDEX idx_level (level),
    INDEX idx_page (page_index),
    INDEX idx_sort (document_context_id, sort_order),
    INDEX idx_path (path(255)),
    INDEX idx_created (created_at),

    -- 全文索引（支持大纲标题搜索）
    FULLTEXT INDEX ft_title (title)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
  COMMENT='大纲表'
  ROW_FORMAT=DYNAMIC;
CREATE DATABASE IF NOT EXISTS stock_agent DEFAULT CHARACTER SET utf8mb4;
USE stock_agent;

-- 차트정보: 날짜/종목번호/종목명/기준가/시작가/저가/고가/(종가)/전날대비등락률/거래량
CREATE TABLE IF NOT EXISTS stock_chart (
  dt          DATE         NOT NULL,
  code        VARCHAR(10)  NOT NULL,
  name        VARCHAR(50)  NOT NULL,
  base_price  DECIMAL(12,2),
  open_price  DECIMAL(12,2),
  low_price   DECIMAL(12,2),
  high_price  DECIMAL(12,2),
  close_price DECIMAL(12,2),
  change_rate DECIMAL(7,2),
  volume      BIGINT,
  PRIMARY KEY (dt, code)
);

-- 이슈정보: 날짜/종목번호/링크주소/내용
CREATE TABLE IF NOT EXISTS stock_issue (
  id      BIGINT AUTO_INCREMENT PRIMARY KEY,
  dt      DATE          NOT NULL,
  code    VARCHAR(10)   NOT NULL,
  link    VARCHAR(1000) NOT NULL,
  content TEXT,
  INDEX idx_issue (dt, code)
);

-- 분석결과: 날짜/종목번호/분석내용
CREATE TABLE IF NOT EXISTS stock_analysis (
  dt      DATE        NOT NULL,
  code    VARCHAR(10) NOT NULL,
  content TEXT,
  PRIMARY KEY (dt, code)
);

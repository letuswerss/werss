import fs from 'fs-extra';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const distDir = path.resolve(__dirname, '../dist');
const targetDir = path.resolve(__dirname, '../../static');

async function copyBuildFiles() {
  try {
    // 检查 dist 目录是否存在
    if (!(await fs.pathExists(distDir))) {
      console.error('❌ dist 目录不存在，请先运行构建命令');
      process.exit(1);
    }

    // 清空目标目录
    if (await fs.pathExists(targetDir)) {
      await fs.emptyDir(targetDir);
      console.log('📁 已清空 static 目录');
    } else {
      await fs.ensureDir(targetDir);
    }

    // 复制文件
    await fs.copy(distDir, targetDir);
    console.log('✅ 构建文件已复制到 static 目录');
  } catch (error) {
    console.error('❌ 复制文件失败:', error);
    process.exit(1);
  }
}

copyBuildFiles();

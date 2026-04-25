import { exec } from 'child_process';
import { promisify } from 'util';
import * as fs from 'fs';
import * as path from 'path';

const execAsync = promisify(exec);

export async function runTests(): Promise<string> {
  try {
    const { stdout, stderr } = await execAsync('pnpm run test -- tests/auto-fix.spec.ts', {
      cwd: process.cwd(),
      maxBuffer: 10 * 1024 * 1024
    });
    return stdout + stderr;
  } catch (error: any) {
    return error.stdout + error.stderr;
  }
}

export async function applyFixes(): Promise<string> {
  try {
    const { stdout, stderr } = await execAsync('pnpm run fix:apply', {
      cwd: process.cwd(),
      maxBuffer: 10 * 1024 * 1024
    });
    return stdout + stderr;
  } catch (error: any) {
    return error.stdout + error.stderr;
  }
}

export function getReport(): any {
  const reportPath = path.join(process.cwd(), 'test-results', 'auto-fix-report.json');
  if (fs.existsSync(reportPath)) {
    return JSON.parse(fs.readFileSync(reportPath, 'utf-8'));
  }
  return null;
}


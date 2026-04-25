#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub 更新工具
用于从 GitHub 仓库更新源码
"""

import os
import subprocess
import logging
import json
from typing import Dict, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class GitHubUpdater:
    """GitHub 仓库更新器"""
    
    def __init__(self, repo_path: str = None):
        """
        初始化更新器
        
        Args:
            repo_path: 仓库路径，默认为当前目录
        """
        self.repo_path = repo_path or os.getcwd()
        self.git_executable = self._find_git_executable()
        
    def _find_git_executable(self) -> str:
        """查找 Git 可执行文件"""
        try:
            # 在 Windows 上尝试 git
            result = subprocess.run(['git', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return 'git'
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
            
        # 尝试其他可能的路径
        possible_paths = [
            '/usr/bin/git',
            '/usr/local/bin/git',
            'C:\\Program Files\\Git\\bin\\git.exe',
            'C:\\Program Files (x86)\\Git\\bin\\git.exe'
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
                
        raise FileNotFoundError("未找到 Git 可执行文件")
    
    def _run_git_command(self, args: list, timeout: int = 300) -> Tuple[bool, str, str]:
        """
        执行 Git 命令
        
        Args:
            args: Git 命令参数列表
            timeout: 超时时间（秒）
            
        Returns:
            (成功状态, 标准输出, 错误输出)
        """
        try:
            cmd = [self.git_executable] + args
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            success = result.returncode == 0
            return success, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            return False, "", "命令执行超时"
        except Exception as e:
            return False, "", f"执行错误: {str(e)}"
    
    def check_git_status(self) -> Dict:
        """检查 Git 仓库状态"""
        status_info = {
            'is_git_repo': False,
            'current_branch': None,
            'has_changes': False,
            'remote_url': None,
            'last_commit': None,
            'ahead_commits': 0,
            'behind_commits': 0,
            'error': None
        }
        
        # 检查是否为 Git 仓库
        success, _, _ = self._run_git_command(['rev-parse', '--git-dir'])
        if not success:
            status_info['error'] = '当前目录不是 Git 仓库'
            return status_info
            
        status_info['is_git_repo'] = True
        
        # 获取当前分支
        success, stdout, _ = self._run_git_command(['rev-parse', '--abbrev-ref', 'HEAD'])
        if success:
            status_info['current_branch'] = stdout.strip()
        
        # 获取远程仓库 URL
        success, stdout, _ = self._run_git_command(['config', '--get', 'remote.origin.url'])
        if success:
            status_info['remote_url'] = stdout.strip()
        
        # 检查是否有未提交的更改
        success, stdout, _ = self._run_git_command(['status', '--porcelain'])
        if success:
            status_info['has_changes'] = len(stdout.strip()) > 0
        
        # 获取最新提交信息
        success, stdout, _ = self._run_git_command(['log', '-1', '--format=%H %s'])
        if success:
            status_info['last_commit'] = stdout.strip()
        
        # 检查与远程的差异
        success, stdout, _ = self._run_git_command(['fetch', '--dry-run'])
        if success:
            # 获取 ahead/behind 信息
            success, stdout, _ = self._run_git_command(['rev-list', '--count', '--left-right', f'origin/{status_info["current_branch"]}...HEAD'])
            if success and stdout.strip():
                behind, ahead = stdout.strip().split()
                status_info['behind_commits'] = int(behind)
                status_info['ahead_commits'] = int(ahead)
        
        return status_info
    
    def update_from_github(self, branch: str = None, backup: bool = True) -> Dict:
        """
        从 GitHub 更新代码
        
        Args:
            branch: 目标分支，默认为当前分支
            backup: 是否在更新前创建备份
            
        Returns:
            更新结果字典
        """
        result = {
            'success': False,
            'message': '',
            'backup_created': False,
            'backup_path': None,
            'updated_files': [],
            'error': None
        }
        
        try:
            # 检查仓库状态
            status = self.check_git_status()
            if not status['is_git_repo']:
                result['error'] = '不是 Git 仓库'
                return result
                
            if status['has_changes']:
                result['error'] = '存在未提交的更改，请先提交或暂存'
                return result
            
            target_branch = branch or status['current_branch']
            
            # 创建备份
            if backup:
                backup_path = self._create_backup()
                if backup_path:
                    result['backup_created'] = True
                    result['backup_path'] = backup_path
            
            # 获取远程更新
            success, stdout, stderr = self._run_git_command(['fetch', 'origin'])
            if not success:
                result['error'] = f'获取远程更新失败: {stderr}'
                return result
            
            # 检查是否有更新
            success, stdout, _ = self._run_git_command(['rev-list', '--count', f'HEAD...origin/{target_branch}'])
            if not success:
                result['error'] = '检查更新失败'
                return result
            
            if int(stdout.strip()) == 0:
                result['success'] = True
                result['message'] = '已是最新版本，无需更新'
                return result
            
            # 执行更新
            success, stdout, stderr = self._run_git_command(['pull', 'origin', target_branch])
            if not success:
                result['error'] = f'更新失败: {stderr}'
                return result
            
            # 获取更新的文件列表
            success, stdout, _ = self._run_git_command(['diff', '--name-only', f'HEAD@{1}', 'HEAD'])
            if success:
                result['updated_files'] = stdout.strip().split('\n') if stdout.strip() else []
            
            result['success'] = True
            result['message'] = f'成功更新 {len(result["updated_files"])} 个文件'
            
        except Exception as e:
            result['error'] = f'更新过程中发生错误: {str(e)}'
            
        return result
    
    def _create_backup(self) -> Optional[str]:
        """创建代码备份"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f'backup_{timestamp}'
            backup_path = os.path.join(os.path.dirname(self.repo_path), backup_name)
            
            success, _, stderr = self._run_git_command(['clone', self.repo_path, backup_path])
            if success:
                logger.info(f'备份创建成功: {backup_path}')
                return backup_path
            else:
                logger.error(f'备份创建失败: {stderr}')
                return None
                
        except Exception as e:
            logger.error(f'创建备份时发生错误: {str(e)}')
            return None
    
    def get_commit_history(self, limit: int = 10) -> list:
        """获取提交历史"""
        commits = []
        
        success, stdout, _ = self._run_git_command([
            'log', 
            f'--oneline', 
            f'-{limit}',
            '--format=%H|%s|%an|%ad',
            '--date=iso'
        ])
        
        if success:
            for line in stdout.strip().split('\n'):
                if line.strip():
                    parts = line.strip().split('|', 3)
                    if len(parts) >= 4:
                        commits.append({
                            'hash': parts[0],
                            'message': parts[1],
                            'author': parts[2],
                            'date': parts[3]
                        })
        
        return commits
    
    def rollback_to_commit(self, commit_hash: str) -> Dict:
        """回滚到指定提交"""
        result = {
            'success': False,
            'message': '',
            'error': None
        }
        
        try:
            # 创建回滚前的备份
            backup_path = self._create_backup()
            
            # 执行回滚
            success, _, stderr = self._run_git_command(['reset', '--hard', commit_hash])
            if not success:
                result['error'] = f'回滚失败: {stderr}'
                return result
            
            result['success'] = True
            result['message'] = f'已回滚到提交 {commit_hash[:8]}'
            if backup_path:
                result['message'] += f'，备份保存在: {backup_path}'
                
        except Exception as e:
            result['error'] = f'回滚过程中发生错误: {str(e)}'
            
        return result


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='GitHub 更新工具')
    parser.add_argument('--path', '-p', help='仓库路径')
    parser.add_argument('--branch', '-b', help='目标分支')
    parser.add_argument('--no-backup', action='store_true', help='不创建备份')
    parser.add_argument('--status', '-s', action='store_true', help='检查状态')
    parser.add_argument('--history', '-n', type=int, default=10, help='显示提交历史数量')
    
    args = parser.parse_args()
    
    updater = GitHubUpdater(args.path)
    
    if args.status:
        status = updater.check_git_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))
    elif args.history:
        commits = updater.get_commit_history(args.history)
        print(json.dumps(commits, indent=2, ensure_ascii=False))
    else:
        result = updater.update_from_github(
            branch=args.branch,
            backup=not args.no_backup
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
import sys
import platform
import subprocess
import os
import glob

def docx_to_pdf(input_path, output_path):
    """
    将指定的 docx 文件转换为 pdf 文件
    :param input_path: 输入的 docx 文件路径
    :param output_path: 输出的 pdf 文件路径
    """
    if platform.system() == "Windows":
        try:
            import pythoncom
            pythoncom.CoInitialize()
            from docx2pdf import convert
            # 使用 docx2pdf 进行转换
            convert(input_path, output_path)
            print(f"成功将 {input_path} 转换为 {output_path}")
            pythoncom.CoUninitialize()
        except Exception as e:
            print(f"转换失败: {e}")
    else:
        try:
            # 使用 libreoffice 进行转换
            subprocess.run(["libreoffice", "--headless", "--convert-to", "pdf", input_path, "--outdir", os.path.dirname(output_path)])
            print(f"成功将 {input_path} 转换为 {output_path}")
        except Exception as e:
            print(f"转换失败: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("用法: python docx2pdf.py <input.docx> <output.pdf>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    docx_to_pdf(input_file, output_file)
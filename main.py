"""
多模态智能反诈助手 - FastAPI 入口

用法：
  python main.py                    # 启动 API 服务
  python main.py --host 0.0.0.0     # 指定主机
  python main.py --port 8000        # 指定端口
"""
import sys
import argparse


def run_api(host: str = "127.0.0.1", port: int = 8000):
    """启动 FastAPI 服务"""
    import uvicorn
    print("=" * 50)
    print("多模态智能反诈助手 API 服务")
    print(f"地址: http://{host}:{port}")
    print(f"文档: http://{host}:{port}/docs")
    print("=" * 50)
    uvicorn.run("api.app:app", host=host, port=port, reload=True)


def main():
    parser = argparse.ArgumentParser(
        description="多模态智能反诈助手",
    )
    parser.add_argument("--host", default="127.0.0.1",
                       help="API 服务主机地址")
    parser.add_argument("--port", type=int, default=8000,
                       help="API 服务端口")

    args = parser.parse_args()
    run_api(host=args.host, port=args.port)


if __name__ == "__main__":
    main()

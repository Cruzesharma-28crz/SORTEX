"""Command-line interface."""

import argparse
import json

from sortex.evaluation import evaluate
from sortex.inference import predict
from sortex.simulation import route_prediction
from sortex.training import train


def build_parser():
    parser = argparse.ArgumentParser(prog="sortex", description="SORTEX waste vision prototype")
    commands = parser.add_subparsers(dest="command", required=True)
    training = commands.add_parser("train", help="train the custom CNN")
    training.add_argument("--data", required=True)
    training.add_argument("--output", required=True)
    training.add_argument("--epochs", type=int, default=30)
    training.add_argument("--batch-size", type=int, default=32)
    testing = commands.add_parser("evaluate", help="evaluate on a held-out folder")
    testing.add_argument("--data", required=True)
    testing.add_argument("--checkpoint", required=True)
    prediction = commands.add_parser("predict", help="classify one image")
    prediction.add_argument("image")
    prediction.add_argument("--checkpoint", required=True)
    prediction.add_argument("--threshold", type=float, default=0.65)
    simulation = commands.add_parser("simulate", help="simulate a decision without hardware")
    simulation.add_argument("--class", dest="label", required=True)
    simulation.add_argument("--confidence", type=float, required=True)
    simulation.add_argument("--threshold", type=float, default=0.65)
    return parser


def main():
    args = build_parser().parse_args()
    if args.command == "train":
        train(args.data, args.output, args.epochs, args.batch_size)
    elif args.command == "evaluate":
        print(json.dumps(evaluate(args.data, args.checkpoint), indent=2))
    elif args.command == "predict":
        print(json.dumps(predict(args.image, args.checkpoint, args.threshold), indent=2))
    elif args.command == "simulate":
        print(json.dumps(route_prediction(args.label, args.confidence, args.threshold), indent=2))


if __name__ == "__main__":
    main()

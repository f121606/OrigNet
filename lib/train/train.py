import os
import sys
sys.path.append(".")
sys.path.append("../../")
sys.path.append("../../../")

import torch
from yacs.config import CfgNode

from lib.config.config import pth
from lib.datasets.make_datasets import make_data_loader
from lib.models.make_network import make_network
from lib.train.scheduler import make_lr_scheduler
from lib.train.optimizers import make_optimizer
from lib.train.trainers.make_trainer import make_trainer
from lib.train.recorder import make_recorder
from lib.utils.net_utils import load_model, save_model


def train(cfg: CfgNode) -> None:
    """訓練と検証を行い，任意のエポック数ごとに訓練されたネットワークを保存する関数．

    Args:
        cfg (CfgNode): `config` 情報が保存された辞書．
    """
    if "train" not in cfg:
        raise ("The training configuration is not set.")

    # cuda が存在する場合，cudaを使用する
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    torch.multiprocessing.set_sharing_strategy("file_system")
    train_loader = make_data_loader(cfg, is_train=True, max_iter=cfg.ep_iter)
    val_loader = make_data_loader(cfg, is_train=False)

    cfg.num_classes = len(train_loader.dataset.classes)
    network = make_network(cfg).to(device)

    trainer = make_trainer(cfg, network)
    optimizer = make_optimizer(cfg, network)
    scheduler = make_lr_scheduler(cfg, optimizer)
    recorder = make_recorder(cfg)

    begin_epoch = load_model(
        network, optimizer, scheduler, recorder, cfg.model_dir, resume=cfg.resume
    )

    for epoch in range(begin_epoch, cfg.train.epoch):
        recorder.epoch = epoch
        trainer.train(epoch, train_loader, optimizer, recorder)
        scheduler.step()

        # 訓練途中のモデルを保存する
        if (epoch + 1) % cfg.save_ep == 0:
            save_model(
                network, optimizer, scheduler, recorder, epoch + 1, cfg.model_dir
            )

        # 検証
        if (epoch + 1) % cfg.eval_ep == 0:
            trainer.val(epoch, val_loader, recorder=recorder)

    # 訓練終了後のモデルを保存
    save_model(network, optimizer, scheduler, recorder, epoch, cfg.model_dir)
    # trainer.val(epoch, val_loader, evaluator, recorder)
    return network


def main(cfg):
    # データの保存先を設定
    cfg.model_dir = os.path.join(
        pth.DATA_DIR, "trained", cfg.task, cfg.model, cfg.model_dir
    )
    cfg.record_dir = os.path.join(
        pth.DATA_DIR, "trained", cfg.task, cfg.model, cfg.record_dir
    )
    # 訓練
    train(cfg)


if __name__ == "__main__":
    # テスト
    import traceback
    from yacs.config import CfgNode as CN

    cfg = CN()
    cfg.task = "classify"
    cfg.network = "cnns"
    cfg.model = "res_34"
    cfg.model_dir = "model"
    cfg.train_type = "transfer"  # or scratch
    # cfg.train_type = "scratch"
    cfg.num_classes = 2
    cfg.img_width = 200
    cfg.img_height = 200
    cfg.resume = True  # 追加学習するか
    cfg.record_dir = "record"
    cfg.ep_iter = -1
    cfg.save_ep = 5
    cfg.eval_ep = 1
    cfg.train = CN()
    cfg.train.epoch = 30
    cfg.train.dataset = "NIVTrain"
    cfg.train.batch_size = 10
    cfg.train.num_workers = 4
    cfg.train.batch_sampler = "image_size"
    cfg.train.optim = "adam"
    cfg.train.criterion = ""
    cfg.train.lr = 1e-3
    cfg.train.scheduler = "step_lr"
    cfg.train.weight_decay = 0.0
    cfg.train.milestones = (20, 40, 60, 80, 100, 120, 160, 180, 200, 220)
    cfg.train.gamma = 0.5
    cfg.test = CN()
    cfg.test.dataset = "NIVTest"
    cfg.test.batch_size = 20
    cfg.test.num_workers = 2
    cfg.test.batch_sampler = "image_size"

    torch.cuda.empty_cache()
    try:
        main(cfg)
    except:
        traceback.print_exc()
    finally:
        torch.cuda.empty_cache()

import sys

sys.path.append(".")
sys.path.append("../../../")

from lib.models.res.resnet import get_res_net as get_res

_network_factory = {
    "res": get_res,
}


def get_network(cfg):
    # from .resnet import get_res_net as get_res

    # _network_factory = {
    #    "res": get_res,
    # }
    arch = cfg.model
    if arch.find("_"):
        num_layers = int(arch[arch.find("_") + 1 :]) if "_" in arch else 0
        arch = arch[: arch.find("_")]

    if arch not in _network_factory:
        raise ValueError(f"The specified cfg.network={arch} does not exist.")

    if "num_classes" not in cfg and "train_type" not in cfg:
        raise ValueError("The required config parameter for `get_network` is not set.")
    get_model = _network_factory[arch]

    # 転移学習を行う場合
    if "transfer" in cfg.train_type:
        model = get_model(num_layers, pretrained=True)
    elif "scratch" in cfg.train_type and int(cfg.num_classes) > 0:
        model = get_model(num_layers, pretrained=False, num_classes=cfg.num_classes)
    else:
        raise ValueError(f"The specified cfg.network={cfg.train_type} does not exist.")

    return model

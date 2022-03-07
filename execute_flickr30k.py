import os
from pycocotools.coco import COCO
from torchvision import transforms, utils
import torch
from dataloader_flickr30k import flickr30kData, collate_fn
from model import Encoder, DecoderWithAttention
from train import *
from voc_flickr30k import build_voc
import argparse
from evaluate_flickr30k import test


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Some description.")

    parser.add_argument("--anns_path", type=str,
                        default="C:\\Users\\doris\\Downloads\\flickr30k\\annotations\\annotations.token")
    parser.add_argument("--image_path", type=str,
                        default="C:\\Users\\doris\\Downloads\\flickr30k\\images")
    parser.add_argument("--test_info", type=str,
                        default="C:\\Users\\doris\\Downloads\\flickr8k\\test_caption_coco_format.json")
    parser.add_argument("--test_path", type=str,
                        default="C:\\Users\\doris\\Downloads\\flickr8k\\Images")
    parser.add_argument("--nmin", type=int,
                        default=50)
    parser.add_argument("--batch_size", type=int,
                        default=32)
    parser.add_argument(
        "--deterministic", action="store_false", help="Whether to shuffle the data. Default is True.",
    )
    parser.add_argument(
        "--fine_tune_encoder", action="store_false", help="",
    )
    parser.add_argument("--num_workers", type=int,
                        default=1)
    parser.add_argument("--emb_dim", type=int,
                        default=512)
    parser.add_argument("--attention_dim", type=int,
                        default=512)
    parser.add_argument("--decoder_dim", type=int,
                        default=512)
    parser.add_argument("--dropout", type=float,
                        default=0.5)
    parser.add_argument("--max_length", type=int,
                        default=25)
    parser.add_argument("--nepoch", type=int,
                        default=15)
    parser.add_argument("--encoder_lr", type=float,
                        default=0.0001)
    parser.add_argument("--decoder_lr", type=float,
                        default=0.0004)
    parser.add_argument("--beam_size", type=int,
                        default=25)

    parser.add_argument("--encoder_save_path", type=str,
                        default="C:\\Users\\doris\\Downloads\\encoder.pth")
    parser.add_argument("--decoder_save_path", type=str,
                        default="C:\\Users\\doris\\Downloads\\decoder.pth")
    parser.add_argument("--log_save_path", type=str,
                        default="C:\\Users\\doris\\Downloads\\log.txt")

    args = parser.parse_args()


    voc = build_voc(args.anns_path, args.nmin)
    dataset = flickr30kData(args.image_path, args.anns_path, voc,
                       transform=transforms.Compose([transforms.Resize((256, 256)), transforms.ToTensor()]))
    dataset_length = len(dataset)
    val_data_len = int(dataset_length/10)
    train_data_len = dataset_length - val_data_len
    train_data, val_data = torch.utils.data.random_split(dataset, [train_data_len, val_data_len])
    train_data = torch.utils.data.DataLoader(train_data, batch_size=args.batch_size, shuffle=args.deterministic,
                                             num_workers=args.num_workers, collate_fn=collate_fn)
    val_data = torch.utils.data.DataLoader(val_data, batch_size=args.batch_size, shuffle=args.deterministic,
                                           num_workers=args.num_workers, collate_fn=collate_fn)

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    # encoder = Encoder(embed_size=args.embed_size).to(device)
    # decoder = Decoder(embed_size=args.embed_size, hidden_size=args.hidden_size, voc_size=len(voc),
    #                   max_length=args.max_length).to(device)
    decoder = DecoderWithAttention(attention_dim=args.attention_dim,
                                   embed_dim=args.emb_dim,
                                   decoder_dim=args.decoder_dim,
                                   vocab_size=len(voc),
                                   dropout=args.dropout)
    decoder_optimizer = torch.optim.Adam(params=filter(lambda p: p.requires_grad, decoder.parameters()),
                                         lr=args.decoder_lr)
    encoder = Encoder()
    encoder.fine_tune(args.fine_tune_encoder)
    encoder_optimizer = torch.optim.Adam(params=filter(lambda p: p.requires_grad, encoder.parameters()),
                                         lr=args.encoder_lr) if args.fine_tune_encoder else None

    # torch.cuda.empty_cache()
    train(encoder, decoder, train_data, val_data, device, args.lr, args.encoder_save_path, args.decoder_save_path, args.nepoch, args.log_save_path)
    test(args.test_info, args.test_path, device, args.embed_size, args.hidden_size, args.max_length, batch_size=args.batch_size, beam_size=args.beam_size, deterministic=args.deterministic, num_workers=args.num_workers,
         encoder_save_path=args.encoder_save_path, decoder_save_path=args.decoder_save_path)
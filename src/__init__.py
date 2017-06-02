import tensorflow as tf
from time import time

from ai_server import AIServer
from ddqrn_trainer import DDQRNTrainer
from evolution_trainer import EvolutionHost
from log_parser import parse_logs_in_folder
from model_saver import ModelSaver
from sharpshooter_server import SharpShooterServer
from simple_ddqrn import DDQRN
from target_ddqrn import target_ddqrn
import parameter_config as cfg
from tournament_selection_server import TournamentSelectionServer

sess = tf.Session()

ddqrn = DDQRN(sess, "main_DDQRN")
ddqrn_target = target_ddqrn(DDQRN(sess, "target_DDQRN"),
                            [tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES, scope="main_DDQRN"),
                             tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES, scope="target_DDQRN")])

sess.run(tf.global_variables_initializer())

#ddqrn_target.update(sess)  # Apparently not necessary

trainer = DDQRNTrainer(ddqrn, ddqrn_target, sess)

model = ModelSaver(ddqrn, trainer)


if cfg.load_model:
    model.load(cfg.save_path)

initial_count = ddqrn.sess.run([ddqrn.train_count])[0]
print("Loading logs...")
logs = parse_logs_in_folder(cfg.log_folder)
print("Training on %s game logs" % len(logs))
time_file = open('times.dat', 'w')
for p, log_file_pair in enumerate(logs):
    start_time = time()
    if p < initial_count:
        print("Skipping log number %s" % p)
        continue
    log_file_0, log_file_1 = log_file_pair
    print("Training on log number %s..." % p, end="", flush=True)
    trainer.start_episode()
    for i, event in enumerate(log_file_0):
        next_event = log_file_0[i + 1]
        # Observe play
        s = event.get_feature_vector()
        a = event.action
        s1 = next_event.get_feature_vector()
        r = next_event.reward

        end = next_event.end

        if r > 0:
            print(" Ooh reward!...", end="", flush=True)

        trainer.experience(s, a, r, s1, end)
        if end:
            break

    train_count = ddqrn.sess.run([ddqrn.inc_train_count])[0]
    trainer.end_episode()
    print(" Done!")
    end_time = time()
    print("Training took %s seconds" % (end_time - start_time))
    time_file.write("%s %s\n" % (p, end_time - start_time))

    # Periodically save the model.
    if p % 50 == 0:
        model.save(cfg.save_path)
        print("Saved Model")
time_file.close()
model.save(cfg.save_path)
print("Done training!")


if cfg.server == cfg.evolution:
    host = EvolutionHost("host", model)
    population = [host.individual.generate_offspring(i) for i in range(cfg.population_size(0))]
    ai_server = TournamentSelectionServer(ddqrn, ddqrn_target, population, model, trainer.train_writer)
elif cfg.server == cfg.gradient:
    ai_server = AIServer(cfg.features, cfg.prediction_to_action, trainer, ddqrn, cfg.rew_funcs, model)

model.ai_server = ai_server


# Assuming we have now done some kind of training.. Try to predict some actions!


server = SharpShooterServer()
server.start()
print("started Server")
i = ddqrn.sess.run([ddqrn.train_count])[0]
while True:
    server.receive_message(ai_server)
    if ai_server.game_has_ended:
        if i % 500 == 0 and type(ai_server) is AIServer:
            ai_server.start_evaluation(200)
        i += 1

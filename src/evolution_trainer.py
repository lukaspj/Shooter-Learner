import tensorflow as tf
import numpy as np
import parameter_config as cfg


class Individual:
    def __init__(self, variables, mutations, name):
        self.variables = variables
        self.mutations = mutations
        self.name = name

    def generate_offspring(self, name):
        n = 0
        for var in self.variables:
            n += var.size
        N = np.random.normal()
        tau = 1/np.sqrt(2*np.sqrt(n))
        tau_prime = 1/np.sqrt(2*n)
        new_variables = []
        new_mutations = []
        for var, mut in zip(self.variables, self.mutations):
            shape = var.shape
            var_flat = var.flatten()
            mut_flat = mut.flatten()
            for var_ny, mut_ny in zip(np.nditer(mut_flat, op_flags=["readwrite"]),
                    np.nditer(var_flat, op_flags=["readwrite"])):
                Nj = np.random.normal()
                mut_ny[...] = mut_ny * np.exp(tau_prime*N+tau*Nj)
                var_ny[...] = var_ny + mut_ny*Nj

            newVar = var_flat.reshape(shape)
            newMut = mut_flat.reshape(shape)
            new_variables.append(newVar)
            new_mutations.append(newMut)

        return Individual(new_variables, new_mutations, str(self.name) + "_" + str(name))


class EvolutionHost:

    def __init__(self, name, model):
        self.sess = tf.Session()
        #self.saver = tf.train.import_meta_graph(path + ".meta")
        self.model = model
        if cfg.load_model:
            ckpt = tf.train.get_checkpoint_state(cfg.save_path)
            self.model.restore(self.sess, ckpt.model_checkpoint_path)

        self.variable_tensors = tf.get_collection(tf.GraphKeys.TRAINABLE_VARIABLES, scope="main_DDQRN")
        self.variables = []
        self.mutations = []
        self.name = name
        self.fitness = None
        for var in self.variable_tensors:
            np_var = np.array(self.sess.run(var))
            self.variables.append(np_var)
            self.mutations.append(np.random.normal(size=np_var.shape))

        self.individual = Individual(self.variables, self.mutations, self.name)


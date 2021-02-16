import covasim as cv
import sciris as sc
import matplotlib.pyplot as plt
import numpy as np


do_plot   = 1
do_show   = 0
do_save   = 1


def test_2strains(do_plot=False, do_show=True, do_save=False):
    sc.heading('Run basic sim with 2 strains')
    sc.heading('Setting up...')

    strains = {'beta': 0.025,
               'rel_severe_prob': 1.3, # 30% more severe across all ages
               'half_life': dict(asymptomatic=20, mild=80, severe=200),
               'init_immunity': 0.9
               }

    pars = {
        'beta': 0.016,
        'n_days': 80,
        'strains': strains,
    }

    sim = cv.Sim(pars=pars)
    sim['immunity'][0,1] = 0.0 # Say that strain A gives no immunity to strain B
    sim['immunity'][1,0] = 0.9 # Say that strain B gives high immunity to strain A
    sim.run()

    strain_labels = [
        f'Strain A: beta {sim["beta"][0]}, half_life {sim["half_life"][0]}',
        f'Strain B: beta {sim["beta"][1]}, half_life {sim["half_life"][1]}',
    ]

    if do_plot:
        sim.plot_result('new_reinfections', do_show=do_show, do_save=do_save, fig_path=f'results/test_2strains.png')
        plot_results(sim, key='incidence_by_strain', title=f'2 strain test, A->B immunity {sim["immunity"][0,1]}, B->A immunity {sim["immunity"][1,0]}', filename='test_2strains2', labels=strain_labels, do_show=do_show, do_save=do_save)
    return sim


def test_importstrain1(do_plot=False, do_show=True, do_save=False):
    sc.heading('Test introducing a new strain partway through a sim')
    sc.heading('Setting up...')

    strain_labels = [
        'Strain 1: beta 0.016',
        'Strain 2: beta 0.025'
    ]

    imported_strain = {
        'beta': 0.025,
        'half_life': dict(asymptomatic=10, mild=50, severe=150),
        'init_immunity': 0.9
    }

    imports = cv.import_strain(strain=imported_strain, days=30, n_imports=30)
    sim = cv.Sim(interventions=imports, label='With imported infections')
    sim.run()

    if do_plot:
        plot_results(sim, key='incidence_by_strain', title='Imported strain on day 30 (cross immunity)', filename='test_importstrain1', labels=strain_labels, do_show=do_show, do_save=do_save)
        plot_shares(sim, key='new_infections', title='Shares of new infections by strain', filename='test_importstrain1_shares', do_show=do_show, do_save=do_save)
    return sim


def test_importstrain2(do_plot=False, do_show=True, do_save=False):
    sc.heading('Test introducing a new strain partway through a sim with 2 strains')
    sc.heading('Setting up...')

    strain2 = {'beta': 0.025,
               'rel_severe_prob': 1.3,
               'half_life': dict(asymptomatic=20, mild=80, severe=200),
               'init_immunity': 0.9
               }
    pars = {
        'n_days': 80,
        'strains': strain2,
    }
    strain3 = {
        'beta': 0.05,
        'rel_symp_prob': 1.6,
        'half_life': dict(asymptomatic=10, mild=50, severe=150),
        'init_immunity': 0.4
    }

    imports = cv.import_strain(strain=strain3, days=10, n_imports=20)
    sim = cv.Sim(pars=pars, interventions=imports, label='With imported infections')
    sim.run()

    strain_labels = [
        'Strain 1: beta 0.016',
        'Strain 2: beta 0.025',
        'Strain 3: beta 0.05, 20 imported day 10'
    ]

    if do_plot:
        plot_results(sim, key='incidence_by_strain', title='Imported strains', filename='test_importstrain2', labels=strain_labels, do_show=do_show, do_save=do_save)
        plot_shares(sim, key='new_infections', title='Shares of new infections by strain',
                filename='test_importstrain2_shares', do_show=do_show, do_save=do_save)
    return sim


def test_par_refactor():
    '''
    The purpose of this test is to experiment with different representations of the parameter structures
    Still WIP!
    '''

    # Simplest case: add a strain to beta
    p1 = cv.Par(name='beta', val=0.016, by_strain=True)
    print(p1.val) # Prints all the stored values of beta
    print(p1[0])  # Can index beta like an array to pull out strain-specific values
    p1.add_strain(new_val = 0.025)

    # Complex case: add a strain that's differentiated by severity for kids 0-20
    p2 = cv.Par(name='sus_ORs', val=np.array([0.34, 0.67, 1., 1., 1., 1., 1.24, 1.47, 1.47, 1.47]), by_strain=True, by_age=True)
    print(p2.val) # Prints all the stored values for the original strain
    print(p2[0])  # Can index beta like an array to pull out strain-specific values
    p2.add_strain(new_val=np.array([1., 1., 1., 1., 1., 1., 1.24, 1.47, 1.47, 1.47]))

    # Complex case: add a strain that's differentiated by duration of disease
    p3 = cv.Par(name='dur_asym2rec', val=dict(dist='lognormal_int', par1=8.0,  par2=2.0), by_strain=True, is_dist=True)
    print(p3.val) # Prints all the stored values for the original strain
    print(p3[0])  # Can index beta like an array to pull out strain-specific values
    p3.add_strain(new_val=dict(dist='lognormal_int', par1=12.0,  par2=2.0))
    p3.get(strain=1, n=6)

    return p1, p2, p3


def test_halflife_by_severity(do_plot=False, do_show=True, do_save=False):
    sc.heading('Run basic sim with 2 strains and half life by severity')
    sc.heading('Setting up...')

    strains = {'half_life': dict(asymptomatic=100, mild=150, severe=200)}

    pars = {
        'n_days': 80,
        'beta': 0.015,
        'strains': strains,
    }

    sim = cv.Sim(pars=pars)
    sim['immunity'][0,1] = 0.0 # Say that strain A gives no immunity to strain B
    sim['immunity'][1,0] = 0.0 # Say that strain B gives no immunity to strain A
    sim.run()

    strain_labels = [
        f'Strain A: beta {pars["beta"]}, half_life not by severity',
        f'Strain B: beta {pars["beta"]}, half_life by severity',
    ]

    if do_plot:
        sim.plot_result('new_reinfections', fig_path='results/test_halflife_by_severity.png', do_show=do_show, do_save=do_save)
        plot_results(sim, key='incidence_by_strain', title=f'2 strain test, A->B immunity {sim["immunity"][0,1]}, B->A immunity {sim["immunity"][1,0]}', filename='test_halflife_by_severity', labels=strain_labels, do_show=do_show, do_save=do_save)
    return sim


def plot_results(sim, key, title, filename=None, do_show=True, do_save=False, labels=None):

    results = sim.results
    results_to_plot = results[key]

    # extract data for plotting
    x = sim.results['t']
    y = results_to_plot.values
    y = np.transpose(y)

    fig, ax = plt.subplots()
    ax.plot(x, y)

    ax.set(xlabel='Day of simulation', ylabel=results_to_plot.name, title=title)

    if labels is None:
        labels = [0]*len(y[0])
        for strain in range(len(y[0])):
            labels[strain] = f'Strain {strain +1}'
    ax.legend(labels)

    if do_show:
        plt.show()
    if do_save:
        cv.savefig(f'results/{filename}.png')

    return


def plot_shares(sim, key, title, filename=None, do_show=True, do_save=False, labels=None):

    results = sim.results
    n_strains = sim.results['new_infections_by_strain'].values.shape[0] # TODO: this should be stored in the sim somewhere more intuitive!
    prop_new = {f'Strain {s}': results[key+'_by_strain'].values[s,1:]/results[key].values[1:] for s in range(n_strains)}
    num_new = {f'Strain {s}': results[key+'_by_strain'].values[s,:] for s in range(n_strains)}

    # extract data for plotting
    x = sim.results['t'][1:]
    fig, ax = plt.subplots(2,1,sharex=True)
    ax[0].stackplot(x, prop_new.values(),
                 labels=prop_new.keys())
    ax[0].legend(loc='upper left')
    ax[0].set_title(title)
    ax[1].stackplot(sim.results['t'], num_new.values(),
                 labels=num_new.keys())
    ax[1].legend(loc='upper left')
    ax[1].set_title(title)

    if do_show:
        plt.show()
    if do_save:
        cv.savefig(f'results/{filename}.png')

    return


#%% Run as a script
if __name__ == '__main__':
    sc.tic()

    sim1 = test_2strains(do_plot=do_plot, do_save=do_save, do_show=do_show)
    sim2 = test_importstrain1(do_plot=do_plot, do_save=do_save, do_show=do_show)
    sim3 = test_importstrain2(do_plot=do_plot, do_save=do_save, do_show=do_show)
    p1, p2, p3 = test_par_refactor()
    sim4 = test_halflife_by_severity(do_plot=do_plot, do_save=do_save, do_show=do_show)

    # simX = test_importstrain_args()

    sc.toc()


print('Done.')



# DEPRECATED
# def test_importstrain_args():
#     sc.heading('Test flexibility of arguments for the import strain "intervention"')
#
#     # Run sim with a single strain initially, then introduce a new strain that's more transmissible on day 10
#     immunity = [
#         {'init_immunity': 1., 'half_life': 180, 'cross_factor': 1},
#     ]
#     pars = {
#         'n_strains': 1,
#         'beta': [0.016],
#         'immunity': immunity
#     }
#
#     # All these should run
#     imports = cv.import_strain(days=50, beta=0.03)
#     #imports = cv.import_strain(days=[10, 50], beta=0.03)
#     #imports = cv.import_strain(days=50, beta=[0.03, 0.05])
#     #imports = cv.import_strain(days=[10, 20], beta=[0.03, 0.05])
#     #imports = cv.import_strain(days=50, beta=[0.03, 0.05, 0.06])
#     #imports = cv.import_strain(days=[10, 20], n_imports=[5, 10], beta=[0.03, 0.05], init_immunity=[1, 1],
#     #                          half_life=[180, 180], cross_factor=[0, 0])
#     #imports = cv.import_strain(days=[10, 50], beta=0.03, cross_factor=[0.4, 0.6])
#     #imports = cv.import_strain(days=['2020-04-01', '2020-05-01'], beta=0.03)
#
#     # This should fail
#     #imports = cv.import_strain(days=[20, 50], beta=[0.03, 0.05, 0.06])
#
#     sim = cv.Sim(pars=pars, interventions=imports)
#     sim.run()
#
#
#     return sim
#

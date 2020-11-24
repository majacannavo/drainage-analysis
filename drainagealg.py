from qgis import processing
from qgis.processing import alg
from qgis.core import QgsProcessingFeedback

@alg(name='drainagealg', label='Compute drainage from DEM (alg)',
     group='myscripts', group_label='My scripts')
     
@alg.input(type=alg.RASTER_LAYER, name='INPUT', label='Input DEM')

@alg.input(type=alg.NUMBER, name='MINSLOPE', label='Min. slope (degrees) for filled DEM',
    default=0.01)

@alg.input(type=alg.ENUM, name='CATCHMENTMETHOD', label='Catchment area method',
    options=['[0] Deterministic 8', '[1] Rho 8', '[2] Braunschweiger Reliefmodell',
        '[3] Deterministic Infinity', '[4] Multiple Flow Direction',
        '[5] Multiple Triangular Flow Direction'],
    default=0)
           
@alg.input(type=alg.NUMBER, name='THRESHOLD', label='Channel initiation threshold',
    default=1000)

@alg.input(type=alg.RASTER_LAYER_DEST, name='FILLED', label='Filled DEM')

@alg.input(type=alg.RASTER_LAYER_DEST, name='FLOWDIR', label='Flow direction')

@alg.input(type=alg.RASTER_LAYER_DEST, name='CATCHMENT', label='Catchment area')

@alg.input(type=alg.RASTER_LAYER_DEST, name='CHANNELSRAST', label='Channel network (raster)')

@alg.input(type=alg.VECTOR_LAYER_DEST, name='CHANNELSVECT', label='Channel network (vector)')


def drainagealg(instance, parameters, context, feedback, inputs):
    """
    This tool employs SAGA terrain analysis tools to compute drainage for a DEM.
    Returns: filled DEM, flow direction, catchment area, raster channel network, and vector channel network.
    
    Author: Maja Cannavo, 2020
    """

    # fill DEM

    filled_result = processing.run("saga:fillsinkswangliu", # SAGA Fill Sinks (wang & liu) tool
        {'ELEV':parameters['INPUT'], # input DEM
        'MINSLOPE':parameters['MINSLOPE'], # min. slope (degrees)
        'FILLED':parameters['FILLED'], # where to save filled DEM
        'FDIR':parameters['FLOWDIR'], # where to save flow direction
        'WSHED':'TEMPORARY_OUTPUT'}, # where to save watershed basins, which we won't be using
        is_child_algorithm=True,
        context=context,
        feedback=feedback) 
    
    if feedback.isCanceled():
        return {}
    
    filled_output = filled_result['FILLED']
    flow_dir = filled_result['FDIR']
    
    feedback.setProgressText('DEM filled')
    
    
    # compute catchment area
    
    catchment_result = processing.run("saga:catchmentarea", # SAGA catchment area tool
        {'ELEVATION':filled_output, # elevation layer
        'METHOD':parameters['CATCHMENTMETHOD'], # method (see options for parameters['CATCHMENTMETHOD'])
        'FLOW':parameters['CATCHMENT']}, # where to save catchment area
        is_child_algorithm=True,
        context=context,
        feedback=feedback) 
    
    if feedback.isCanceled():
        return {}
    
    catchment_output = catchment_result['FLOW']
    
    feedback.setProgressText('Catchment area computed')

   
    # compute channel network
    
    channels_result = processing.run("saga:channelnetwork", # SAGA channel network tool
        {'ELEVATION':filled_output, # elevation layer
        'SINKROUTE':flow_dir, # flow direction layer
        'INIT_GRID':catchment_output, # initiation grid (catchment area)
        'INIT_METHOD':2, # initiation type: greater than
        'INIT_VALUE':parameters['THRESHOLD'], # initiation threshold
        'DIV_GRID':None, # divergence (optional)
        'DIV_CELLS':10, # tracing: max. divergence (optional)
        'TRACE_WEIGHT':None, # tracing: weight (optional)
        'MINLEN':10, # min. segment length
        'CHNLNTWRK':parameters['CHANNELSRAST'], # where to save channel network (raster)
        'CHNLROUTE':'TEMPORARY_OUTPUT', # where to save channel direction, which we won't be using
        'SHAPES':parameters['CHANNELSVECT']}, # where to save channel network (vector)
        is_child_algorithm=True,
        context=context,
        feedback=feedback)
    
    raster_channels = channels_result['CHNLNTWRK']
    vector_channels = channels_result['SHAPES']
    
    if feedback.isCanceled():
        return{}
    
    feedback.setProgressText('Channel network computed')


    # return results
        
    return {'FILLED':filled_output,
        'FLOWDIR':flow_dir,
        'CATCHMENT':catchment_output,
        'CHANNELSRAST':raster_channels,
        'CHANNELSVECT':vector_channels}
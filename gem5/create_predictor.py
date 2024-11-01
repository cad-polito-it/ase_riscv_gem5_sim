from m5.objects.BranchPredictor import *
import os

def create_IndirectPredictor():
    return IndirectPredictor()

def create_SimpleIndirectPredictor():
    pred=SimpleIndirectPredictor()
    pred.indirectHashGHR = True # Hash branch predictor GHR
    pred.indirectHashTargets = True # Hash path history targets
    pred.indirectSets = 256 # Cache sets for indirect predictor
    pred.indirectWays = 2 # Ways for indirect predictor
    pred.indirectTagSize = 16 # Indirect target cache tag bits
    pred.indirectPathLength = 3 # Previous indirect targets to use for path history
    pred.indirectGHRBits = 13 # Indirect GHR number of bits
    pred.instShiftAmt = 2 # Number of bits to shift instructions by
    return pred

def create_BranchPredictor():
    pred=BranchPredictor()
    pred.BTBEntries = 4096 # Number of BTB entries
    pred.BTBTagSize = 16 # Size of the BTB tags, in bits
    pred.RASSize = 16#  RAS size
    pred.instShiftAmt =2 # Number of bits to shift instructions by
    pred.indirectBranchPred = SimpleIndirectPredictor() #Indirect branch predictor, set to NULL to disable indirect predictions
    return pred


def create_LocalBP():
    # LOCAL BP it inherits BranchPredictor (therefore you can also set those parameters)
    pred = LocalBP()
    pred.localPredictorSize = 32
    pred.localCtrBits = 2
    pred.BTBEntries = 256
    return pred

def create_TournamentBP():
    # TOURNAMENT BP it inherits BranchPredictor
    pred = TournamentBP()
    pred.localPredictorSize = 32
    pred.localHistoryTableSize = 256
    pred.globalPredictorSize = 64
    pred.choicePredictorSize = 64
    if os.getenv('IS_DOCKER') != 'true':
        pred.BTBEntries = 256
    pred.localPredictorSize = 2048 # Size of local predictor
    pred.localCtrBits = 2 # Bits per counter
    pred.localHistoryTableSize = 2048 # size of local history table
    pred.globalPredictorSize = 8192 # Size of global predictor
    pred.globalCtrBits = 2 # Bits per counter
    pred.choicePredictorSize =8192 # Size of choice predictor
    pred.choiceCtrBits = 2 # Bits of choice counters
    return pred

def create_BiModeBP():
    # BIMODE BP  it inherits BranchPredictor 
    pred = BiModeBP()
    pred.globalPredictorSize = 64
    pred.choicePredictorSize = 64
    pred.BTBEntries = 256
    pred.globalPredictorSize = 8192 # Size of global predictor
    pred.globalCtrBits = 2 # Bits per counter
    pred.choicePredictorSize = 8192 # Size of choice predictor
    pred.choiceCtrBits = 2 # Bits of choice counters
    return pred 

def create_LTAGE():
    ##fixme it generate a runtime exception in gem5 
    # LTAGE BP
    # LTAGE branch predictor as described in
    # https://www.irisa.fr/caps/people/seznec/L-TAGE.pdf
    # It is basically a TAGE predictor plus a loop predictor
    # The differnt TAGE sizes are updated according to the paper values (256 Kbits)
    pred = LTAGE()
    pred.BTBEntries = 128
    pred.BTBTagSize = 56
    pred.numThreads = 2
    pred.RASSize = 32
    # TAGE Parameters
    pred.tage=LTAGE_TAGE()
    pred.tage.nHistoryTables = 6
    pred.tage.tagTableTagWidths = [0, 7, 7, 8, 8, 9, 9]
    pred.tage.logTagTableSizes = [0, 7, 7, 8, 8, 7, 7]
    pred.tage.logUResetPeriod = 11
    pred.tage.tagTableCounterBits = 3
    pred.tage.tagTableUBits = 2
    # Loop parameters
    pred.loop_predictor = LoopPredictor() # Loop predictor
    pred.loop_predictor.loopTableTagBits = 10
    pred.loop_predictor.loopTableConfidenceBits = 3
    pred.loop_predictor.loopTableAgeBits = 3
    pred.loop_predictor.initialLoopAge = 5
    pred.loop_predictor.logLoopTableAssoc = 4
    pred.loop_predictor.loopTableIterBits = 10
    pred.loop_predictor.logSizeLoopPred = 4
    pred.loop_predictor.withLoopBits = 10
    return pred


def create_TAGEBase():
    pred=TAGEBase()
      
    pred.nHistoryTables = 7 # Number of history tables
    pred.minHist = 5 # Minimum history size of TAGE
    pred.maxHist = 130 # Maximum history size of TAGE

    pred.tagTableTagWidths =   [0, 9, 9, 10, 10, 11, 11, 12] # Tag size in TAGE tag tables
    pred.logTagTableSizes =  [13, 9, 9, 9, 9, 9, 9, 9] # Log2 of TAGE table sizes
    pred.logRatioBiModalHystEntries = 2 # Log num of prediction entries for a shared hysteresis bit for the Bimodal

    pred.tagTableCounterBits = 3 # Number of tag table counter bits
    pred.tagTableUBits = 2 # Number of tag table u bits

    pred.histBufferSize = 2097152 #A large number to track all branch histories(2MEntries default)

    pred.pathHistBits = 16 # Path history sizes
    pred.logUResetPeriod = 18 # Log period in number of branches to reset TAGE useful counters
    pred.numUseAltOnNa = 1  # Number of USE_ALT_ON_NA counters
    pred.initialTCounterValue = 1 << 17 # Initial value of tCounter
    pred.useAltOnNaBits = 4 # Size of the USE_ALT_ON_NA counter(s)

    pred.maxNumAlloc = 1 #Max number of TAGE entries allocted on mispredict

    # List of enabled TAGE tables. If empty, all are enabled
    pred.noSkip =[] # Vector of enabled TAGE tables

    pred.speculativeHistUpdate = True # Use speculative update for histories
    return pred




### tage can be of different class 


# TAGE branch predictor as described in https://www.jilp.org/vol8/v8paper1.pdf
# The default sizes below are for the 8C-TAGE configuration (63.5 Kbits)
def create_TAGE():
    # it inherits BranchPredictor
    pred=TAGE()
    pred.tage=TAGEBase()
    return pred


def create_LoopPredictor():
    pred=LoopPredictor()
    pred.logSizeLoopPred =8 #  Log size of the loop predictor
    pred.withLoopBits =7 #  Size of the WITHLOOP counter
    pred.loopTableAgeBits =8 #  Number of age bits per loop entry
    pred.loopTableConfidenceBits =2 # Number of confidence bits per loop entry
    pred.loopTableTagBits =14  # Number of tag bits per loop entry
    pred.loopTableIterBits =14  # Nuber of iteration bits per loop
    pred.logLoopTableAssoc =2  # Log loop predictor associativity

    # Parameters for enabling modifications to the loop predictor
    # They have been copied from TAGE-GSC-IMLI
    # (http://www.irisa.fr/alf/downloads/seznec/TAGE-GSC-IMLI.tar)
    #
    # All of them should be disabled to match the original LTAGE implementation
    # (http://hpca23.cse.tamu.edu/taco/camino/cbp2/cbp-src/realistic-seznec.h)

    # Add speculation
    pred.useSpeculation = False # Use speculation

    # Add hashing for calculating the loop table index
    pred.useHashing = False # Use hashing

    # Add a direction bit to the loop table entries
    pred.useDirectionBit = False # Use direction info

    # If true, use random to decide whether to allocate or not, and only try
    # with one entry
    pred.restrictAllocation = False # Restrict the allocation conditions

    pred.initialLoopIter =1 # Initial iteration number
    pred.initialLoopAge =255 # Initial age value
    pred.optionalAgeReset =True # Reset age bits optionally in some cases
    return pred
def create_TAGE_SC_L_LoopPredictor():
    ## it inherits LoopPredictor
    pred=TAGE_SC_L_LoopPredictor()
    pred.loopTableAgeBits = 4
    pred.loopTableConfidenceBits = 4
    pred.loopTableTagBits = 10
    pred.loopTableIterBits = 10
    pred.useSpeculation = False
    pred.useHashing = True
    pred.useDirectionBit = True
    pred.restrictAllocation = True
    pred.initialLoopIter = 0
    pred.initialLoopAge = 7
    pred.optionalAgeReset = False
    return pref

def create_TAGE_SC_L_64KB_StatisticalCorrector():
    pred=TAGE_SC_L_64KB_StatisticalCorrector()
    pred.pnb = 3 # Num variation global branch GEHL lengths
    pred.pm =[25, 16, 9] # Variation global branch GEHL lengths
    pred.logPnb = 9 # Log number of variation global branch GEHL entries
    pred.snb =3 # Num second local history GEHL lenghts
    pred.sm = [16, 11, 6] # Second local history GEHL lengths
    pred.logSnb = 9 # Log number of second local history GEHL entries
    pred.tnb = 2 # Num third local history GEHL lenghts
    pred.tm = [9, 4] # Third local history GEHL lengths
    pred.logTnb = 10 # Log number of third local history GEHL entries
    pred.imnb = 2 # Num second IMLI GEHL lenghts
    pred.imm = [10, 4] # Second IMLI history GEHL lengths
    pred.logImnb = 9 # Log number of second IMLI GEHL entries
    pred.numEntriesSecondLocalHistories = 16 # Number of entries for second local histories
    pred.numEntriesThirdLocalHistories = 16 # Number of entries for second local histories
    pred.numEntriesFirstLocalHistories = 256 # Number of entries for first local histories
    pred.logBias = 8 #Num global backward branch GEHL lengths
    pred.bwnb = 3 # Global backward branch GEHL lengths
    pred.bwm = [40, 24, 10]
    pred.logBwnb = 10 # Log num of global backward branch GEHL entries
    pred.bwWeightInitValue = 7 # Initial value of the weights of the global backward branch GEHL entries
    pred.lnb = 3 # Num first local history GEHL lenghts
    pred.lm = [11, 6, 3] # First local history GEHL length
    pred.logLnb = 10 # Log number of first local history GEHL entries
    pred.lWeightInitValue = 7 # Initial  value of the weights of the first local history GEHL entries
    pred.logInb = 8 # Log number of IMLI GEHL entries
    pred.iWeightInitValue = 7 # Initial value of the weights of the IMLI history GEHL entries
    pred.inb =1  # Num IMLI GEHL lenghts
    pred.im =[8] #  IMLI history GEHL lengths
    pred.logSizeUp =6 # Log size of update threshold counters tables
    pred.chooserConfWidth = 7 # Number of bits for the chooser counters
    pred.updateThresholdWidth = 12 # Number of bits for the update threshold counter
    pred.pUpdateThresholdWidth = 8 # Number of bits for the pUpdate threshold counters
    pred.extraWeightsWidth = 6 # Number of bits for the extra weights
    pred.scCountersWidth = 6 # Statistical corrector counters width
    pred.initialUpdateThresholdValue = 0 # Initial pUpdate threshold counter value
    return pred

def create_TAGE_SC_L_8KB_StatisticalCorrector():
    pred=TAGE_SC_L_8KB_StatisticalCorrector()
    #it inherits StatisticalCorrector
    pred.gnb = 2# Num global branch GEHL lengths
    pred.gm = [6, 3] # Global branch GEHL lengths
    pred.logGnb = 7 # Log number of global branch GEHL entries
    pred.numEntriesFirstLocalHistories = 64
    pred.logBias = 7
    pred.bwnb = 2
    pred.logBwnb = 7
    pred.bwm = [16, 8]
    pred.bwWeightInitValue = 7
    pred.lnb = 2
    pred.logLnb = 7
    pred.lm = [6, 3]
    pred.lWeightInitValue = 7
    pred.logInb = 7
    pred.iWeightInitValue = 7
    return pred

def create_TAGE_SC_L_64KB():
    pred=TAGE_SC_L_64KB()
    # 64KB TAGE-SC-L branch predictor as described in
    # http://www.jilp.org/cbp2016/paper/AndreSeznecLimited.pdf
    pred.tage = TAGE_SC_L_TAGE_64KB()
    pred.loop_predictor = TAGE_SC_L_64KB_LoopPredictor()
    pred.statistical_corrector = TAGE_SC_L_64KB_StatisticalCorrector()
    return pred


def create_TAGE_SC_L_8KB():
    pred=TAGE_SC_L_8KB()
    # 8KB TAGE-SC-L branch predictor as described in
    # http://www.jilp.org/cbp2016/paper/AndreSeznecLimited.pdf
    pred.tage = TAGE_SC_L_TAGE_8KB()
    pred.loop_predictor = TAGE_SC_L_8KB_LoopPredictor()
    pred.statistical_corrector = TAGE_SC_L_8KB_StatisticalCorrector()
    return pred

def create_MultiperspectivePerceptron():
    pred=MultiperspectivePerceptron()
    # it inherits BranchPredictor
    pred.num_filter_entries = 0 # Number of filter entries
    pred.num_local_histories = 0 # Number of local history entries
    pred.local_history_length = 11 # Length in bits of each history entry
    pred.block_size = 21 # number of ghist bits in a 'block'; this is the width of an initial hash of ghist
    pred.pcshift = -10 # Shift for hashing PC
    pred.threshold = 1 # Threshold for deciding low/high confidence
    pred.bias0 =  -5 # Bias perceptron output this much on all-bits-zero local history
    pred.bias1 = 5 # Bias perceptron output this much on all-bits-one local history
    pred.biasmostly0 = -1 # Bias perceptron output this much on almost-all-bits-zero loca lhistory
    pred.biasmostly1 = 1 # Bias perceptron output this much on almost-all-bits-one local history
    pred.nbest = 20 # Use this many of the top performing tables on a low-confidence branch
    pred.tunebits =24 # Number of bits in misprediction counters
    pred.hshift = -6 # How much to shift initial feauture hash before XORing with PC bits
    pred.imli_mask1 =0 # Which tables should have their indices hashed with the first IMLI counter
    pred.imli_mask4 = 0 # Which tables should have their indices hashed with the fourth IMLI counter
    pred.recencypos_mask =0 # Which tables should have their indices hashed with the recency position
    pred.fudge = 0.245 #  Fudge factor to multiply by perceptron output
    pred.n_sign_bits = 2 # Number of sign bits per magnitude
    pred.pcbit = 2 # Bit from the PC to use for hashing global history
    pred.decay = 0 # Whether and how often to decay a random weight
    pred.record_mask = 191 # Which histories are updated with filtered branch outcomes
    pred.hash_taken = False # Hash the taken/not taken value with a PC bit
    pred.tuneonly = True # If true, only count mispredictions of low-confidence branches
    pred.extra_rounds = 1 # Number of extra rounds of training a single weight on a low-confidence prediction
    pred.speed = 9 # Adaptive theta learning speed
    pred.initial_theta = 10 # Initial theta
    pred.budgetbits = 0 # Hardware budget in bits
    pred.speculative_update = False # Use speculative update for histories
    pred.initial_ghist_length = 1 # Initial GHist length value
    pred.ignore_path_size = False # Ignore the path storage
    return pred


def create_MultiperspectivePerceptron8KB():
    pred=MultiperspectivePerceptron8KB()
    # it inheritsMultiperspectivePerceptron
    pred.budgetbits = 8192 * 8 + 2048
    pred.num_local_histories = 48
    pred.num_filter_entries = 0
    pred.imli_mask1 = 0x6
    pred.imli_mask4 = 0x4400
    pred.recencypos_mask = 0x100000090
    return pred

def create_MultiperspectivePerceptron64KB():
    pred=MultiperspectivePerceptron64KB()
    #it inherits MultiperspectivePerceptron
    pred.budgetbits = 65536 * 8 + 2048
    pred.num_local_histories = 510
    pred.num_filter_entries = 18025
    pred.imli_mask1 = 0xc1000
    pred.imli_mask4 = 0x80008000
    pred.recencypos_mask = 0x100000090
    return pred

def create_MPP_TAGE():
    pred=MPP_TAGE()
    # it inherits TAGEBase
    pred.nHistoryTables = 15
    pred.pathHistBits = 27
    pred.instShiftAmt = 0
    pred.histBufferSize = 16384
    pred.maxHist = 4096
    pred.tagTableTagWidths = [0, 7, 9, 9, 9, 10, 11, 11, 12, 12,
                       12, 13, 14, 15, 15, 15]
    pred.logTagTableSizes = [14, 10, 11, 11, 11, 11, 11, 12, 12,
                         10, 11, 11, 9, 7, 7, 8]
    pred.tunedHistoryLengths = [0, 5, 12, 15, 21, 31, 43, 64,
        93, 137, 200, 292, 424, 612, 877, 1241] # Tuned history lengths
    pred.logUResetPeriod = 10
    pred.initialTCounterValue = 0
    pred.numUseAltOnNa = 512
    pred.speculativeHistUpdate = False
    return pred


def create_MPP_LoopPredictor():
    pred=MPP_LoopPredictor()
    # in inherits LoopPredictor
    pred.useDirectionBit = True
    pred.useHashing = True
    pred.useSpeculation = False
    pred.loopTableConfidenceBits = 4
    pred.loopTableAgeBits = 4
    pred.initialLoopAge = 7
    pred.initialLoopIter = 0
    pred.loopTableIterBits = 12
    pred.optionalAgeReset = False
    pred.restrictAllocation = True
    pred.logSizeLoopPred = 6
    pred.loopTableTagBits = 10


def create_MPP_StatisticalCorrector():
    pred=MPP_StatisticalCorrector()
    # in inherits StatisticalCorrector
    # Unused in this Statistical Corrector
    pred.bwnb = 0
    pred.bwm = [ ]
    pred.logBwnb = 0
    pred.bwWeightInitValue = -1

    # Unused in this Statistical Corrector
    pred.logInb = 0
    pred.iWeightInitValue = -1

    pred.extraWeightsWidth = 0
    pred.pUpdateThresholdWidth = 10
    pred.initialUpdateThresholdValue = 35
    pred.logSizeUp = 5
    pred.lnb = 3
    pred.lm = [11, 6, 3]
    pred.logLnb = 10
    pred.lWeightInitValue = -1
    pred.gnb = 4 # Num global branch GEHL lengths
    pred.gm = [27, 22, 17, 14] # Global branch GEHL lengths
    pred.logGnb = 10 # Log number of global branch GEHL entries
    pred.pnb = 4 # Num variation global branch GEHL lengths
    pred.pm = [16, 11, 6, 3] # Variation global branch GEHL lengths
    pred.logPnb = 9 # Log number of variation global branch GEHL entries
    return pred


def create_MultiperspectivePerceptronTAGE():
    pred=MultiperspectivePerceptronTAGE()
    # it inherits MultiperspectivePerceptron
    pred.instShiftAmt = 4
    pred.imli_mask1 = 0x70
    pred.imli_mask4 = 0
    pred.num_filter_entries = 0
    pred.num_local_histories = 0
    pred.recencypos_mask = 0 # Unused
    pred.threshold = -1
    pred.initial_ghist_length = 0
    pred.ignore_path_size = True
    pred.n_sign_bits = 1
    pred.tage = TAGEBase()
    pred.loop_predictor =LoopPredictor()
    pred.statistical_corrector = StatisticalCorrector()
    return pred


def create_MPP_StatisticalCorrector_64KB():
    pred=MPP_StatisticalCorrector_64KB()
    # it inherits (MPP_StatisticalCorrector
    pred.logBias = 8
    pred.snb = 4 # Num second local history GEHL lenghts
    pred.sm = [16, 11, 6, 3]   # Second local history GEHL lengths
    pred.logSnb = 9 # Log number of second local history GEHL entries
    pred.tnb = 3 # Num third local history GEHL lenghts
    pred.tm = [22, 17, 14] # Third local history GEHL lengths
    pred.logTnb = 9 # Log number of third local history GEHL entries
    pred.numEntriesSecondLocalHistories = 16 # Number of entries for second local histories
    pred.numEntriesThirdLocalHistories = 16 # Number of entries for second local histories
    pred.numEntriesFirstLocalHistories = 256
    return pred


def create_MultiperspectivePerceptronTAGE64KB():
    pred=MultiperspectivePerceptronTAGE64KB()
    #it inherits MultiperspectivePerceptronTAGE
    pred.budgetbits = 65536 * 8 + 2048
    pred.tage = MPP_TAGE()
    pred.loop_predictor = MPP_LoopPredictor()
    pred.statistical_corrector = MPP_StatisticalCorrector_64KB()
    return pred

def create_MPP_LoopPredictor_8KB():
    pred=MPP_LoopPredictor_8KB()
    # it inherits MPP_LoopPredictor
    pred.loopTableIterBits = 10
    pred.logSizeLoopPred = 4
    return pred

def create_MPP_StatisticalCorrector_8KB():
    pred=MPP_StatisticalCorrector_8KB()
    # it inherits MPP_StatisticalCorrector
    pred.logBias = 7
    pred.lnb = 2
    pred.lm = [8, 3]
    pred.logLnb = 9
    pred.logGnb = 9
    pred.logPnb = 7
    pred.numEntriesFirstLocalHistories = 64
    return pred


def create_MultiperspectivePerceptronTAGE8KB():
    pred=MultiperspectivePerceptronTAGE8KB()
    #it inherits (MultiperspectivePerceptronTAGE
    pred.budgetbits = 8192 * 8 + 2048
    pred.tage = MPP_TAGE_8KB()
    pred.loop_predictor = MPP_LoopPredictor_8KB()
    pred.statistical_corrector = MPP_StatisticalCorrector_8KB()
    return pred

### all possible tages that can be used
#
#class MPP_TAGE_8KB(MPP_TAGE):
#    type = 'MPP_TAGE_8KB'
#    cxx_class = 'MPP_TAGE_8KB'
#    cxx_header = 'cpu/pred/multiperspective_perceptron_tage_8KB.hh'
#    nHistoryTables = 10
#    tagTableTagWidths = [0, 7, 7, 7, 8, 9, 10, 10, 11, 13, 13]
#    logTagTableSizes = [12, 8, 8, 9, 9, 8, 8, 8, 7, 6, 7]
#    tunedHistoryLengths = [0, 4, 8, 13, 23, 36, 56, 93, 145, 226, 359]
#
#class TAGE_SC_L_TAGE(TAGEBase):
#    type = 'TAGE_SC_L_TAGE'
#    cxx_class = 'TAGE_SC_L_TAGE'
#    cxx_header = "cpu/pred/tage_sc_l.hh"
#    abstract = True
#    tagTableTagWidths = [0]
#    numUseAltOnNa = 16
#    pathHistBits = 27
#    maxNumAlloc = 2
#    logUResetPeriod = 10
#    initialTCounterValue = 1 << 9
#    useAltOnNaBits = 5
#    # TODO No speculation implemented as of now
#    speculativeHistUpdate = False
#
#    # This size does not set the final sizes of the tables (it is just used
#    # for some calculations)
#    # Instead, the number of TAGE entries comes from shortTagsTageEntries and
#    # longTagsTageEntries
#    logTagTableSize = Param.Unsigned("Log size of each tag table")
#
#    shortTagsTageFactor = Param.Unsigned(
#        "Factor for calculating the total number of short tags TAGE entries")
#
#    longTagsTageFactor = Param.Unsigned(
#        "Factor for calculating the total number of long tags TAGE entries")
#
#    shortTagsSize = Param.Unsigned(8, "Size of the short tags")
#
#    longTagsSize = Param.Unsigned("Size of the long tags")
#
#    firstLongTagTable = Param.Unsigned("First table with long tags")
#
#    truncatePathHist = Param.Bool(True,
#        "Truncate the path history to its configured size")
#
#
#class TAGE_SC_L_TAGE_64KB(TAGE_SC_L_TAGE):
#    type = 'TAGE_SC_L_TAGE_64KB'
#    cxx_class = 'TAGE_SC_L_TAGE_64KB'
#    cxx_header = "cpu/pred/tage_sc_l_64KB.hh"
#    nHistoryTables = 36
#
#    minHist = 6
#    maxHist = 3000
#
#    tagTableUBits = 1
#
#    logTagTableSizes = [13]
#
#    # This is used to handle the 2-way associativity
#    # (all odd entries are set to one, and if the corresponding even entry
#    # is set to one, then there is a 2-way associativity for this pair)
#    # Entry 0 is for the bimodal and it is ignored
#    # Note: For this implementation, some odd entries are also set to 0 to save
#    # some bits
#    noSkip = [0,0,1,0,0,0,1,0,0,1,1,1,1,1,1,1,1,1,1,
#                1,1,1,1,0,1,0,1,0,1,0,0,0,1,0,0,0,1]
#
#    logTagTableSize = 10
#    shortTagsTageFactor = 10
#    longTagsTageFactor = 20
#
#    longTagsSize = 12
#
#    firstLongTagTable = 13
#
#class TAGE_SC_L_TAGE_8KB(TAGE_SC_L_TAGE):
#    type = 'TAGE_SC_L_TAGE_8KB'
#    cxx_class = 'TAGE_SC_L_TAGE_8KB'
#    cxx_header = "cpu/pred/tage_sc_l_8KB.hh"
#
#    nHistoryTables = 30
#
#    minHist = 4
#    maxHist = 1000
#
#    logTagTableSize = 7
#    shortTagsTageFactor = 9
#    longTagsTageFactor = 17
#    longTagsSize = 12
#
#    logTagTableSizes = [12]
#
#    firstLongTagTable = 11
#
#    truncatePathHist = False
#
#    noSkip = [0,0,1,0,1,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,1,0,1,0,1,0,1,0,1]
#
#    tagTableUBits = 2
#
## TAGE-SC-L branch predictor as desribed in
## https://www.jilp.org/cbp2016/paper/AndreSeznecLimited.pdf
## It is a modified LTAGE predictor plus a statistical corrector predictor
## The TAGE modifications include bank interleaving and partial associativity
## Two different sizes are proposed in the paper:
## 8KB => See TAGE_SC_L_8KB below
## 64KB => See TAGE_SC_L_64KB below
## The TAGE_SC_L_8KB and TAGE_SC_L_64KB classes differ not only on the values
## of some parameters, but also in some implementation details
## Given this, the TAGE_SC_L class is left abstract
## Note that as it is now, this branch predictor does not handle any type
## of speculation: All the structures/histories are updated at commit time
#class TAGE_SC_L(LTAGE):
#    type = 'TAGE_SC_L'
#    cxx_class = 'TAGE_SC_L'
#    cxx_header = "cpu/pred/tage_sc_l.hh"
#    abstract = True
#
#    statistical_corrector = Param.StatisticalCorrector(
#        "Statistical Corrector")
#
#class TAGE_SC_L_64KB_LoopPredictor(TAGE_SC_L_LoopPredictor):
#    logSizeLoopPred = 5
#
#class TAGE_SC_L_8KB_LoopPredictor(TAGE_SC_L_LoopPredictor):
#    logSizeLoopPred = 3
#
#
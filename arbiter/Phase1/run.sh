#sst withCache.py --model-options="--packet_count=10000" > with_Cache.log
#sst withoutCache.py --model-options="--packet_count=10000" > without_Cache.log
#sst withCacheMultiCore.py --model-options="--packet_count=10000" #> with_Cache_Multi.log
sst withoutCacheMultiCore.py --model-options="--packet_count=10000" #t> without_Cache_Multi.log
#sst withoutCacheMultiCoreWrongAccess.py --model-options="--packet_count=10000" #t> without_Cache_Multi.log

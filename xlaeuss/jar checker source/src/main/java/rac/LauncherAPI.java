/*
 * Decompiled with CFR 0.153-SNAPSHOT (d6f6758-dirty).
 */
package rac;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import io.netty.bootstrap.Bootstrap;
import io.netty.channel.Channel;
import io.netty.channel.ChannelHandlerContext;
import io.netty.channel.ChannelInitializer;
import io.netty.channel.ChannelPipeline;
import io.netty.channel.SimpleChannelInboundHandler;
import io.netty.channel.nio.NioEventLoopGroup;
import io.netty.channel.socket.SocketChannel;
import io.netty.channel.socket.nio.NioSocketChannel;
import io.netty.handler.codec.serialization.ClassResolvers;
import io.netty.handler.codec.serialization.ObjectDecoder;
import io.netty.handler.codec.serialization.ObjectEncoder;
import java.util.HashMap;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;
import rac.AuthPayloadBuilder;
import rac.CraftRiseCrypto;

public class LauncherAPI {
    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public static String getkeyValidator(final String username, final String password) {
        NioEventLoopGroup group = new NioEventLoopGroup();
        final CompletableFuture future = new CompletableFuture();
        try {
            String sa5;
            Bootstrap b = new Bootstrap();
            ((Bootstrap)((Bootstrap)b.group(group)).channel(NioSocketChannel.class)).handler(new ChannelInitializer<SocketChannel>(){

                @Override
                protected void initChannel(SocketChannel ch) {
                    ChannelPipeline pipeline = ch.pipeline();
                    pipeline.addLast(new ObjectDecoder(ClassResolvers.softCachingResolver(ClassLoader.getSystemClassLoader())));
                    pipeline.addLast(new ObjectEncoder());
                    pipeline.addLast(new SimpleChannelInboundHandler<Object>(){

                        @Override
                        public void channelActive(ChannelHandlerContext ctx) {
                            HashMap<String, String> payload = AuthPayloadBuilder.buildPayload(username, password);
                            String json = String.format("{\n  \"messageType\": \"tryLogin\",\n  \"datas\": {\n    \"sumBigX\": \"%s\",\n    \"password\": \"%s\",\n    \"sumBig\": \"%s\",\n    \"sumBigY\": \"%s\",\n    \"sum\": \"%s\",\n    \"key\": \"%s\",\n    \"username\": \"%s\",\n    \"staticSessionKey\": \"%s\"\n  }\n}", payload.get("sumBigX"), password, payload.get("sumBig"), payload.get("sumBigY"), payload.get("sum"), payload.get("key"), username, payload.get("staticSessionKey"));
                            ctx.writeAndFlush(json + "\n");
                        }

                        @Override
                        protected void channelRead0(ChannelHandlerContext ctx, Object msg) {
                            if (msg instanceof String) {
                                String jsonStr = (String)msg;
                                try {
                                    JsonObject obj = new JsonParser().parse(jsonStr).getAsJsonObject();
                                    if (obj.has("keyValidator")) {
                                        String keyValidator = obj.get("keyValidator").getAsString();
                                        future.complete(keyValidator);
                                    } else if (obj.has("message")) {
                                        future.complete(null);
                                    } else {
                                        future.complete(null);
                                    }
                                } catch (Exception e) {
                                    future.complete(null);
                                }
                                ctx.close();
                            }
                        }

                        @Override
                        public void exceptionCaught(ChannelHandlerContext ctx, Throwable cause) {
                            future.complete(null);
                            ctx.close();
                        }
                    });
                }
            });
            Channel ch = b.connect("185.255.92.10", 4754).sync().channel();
            String result = (String)future.get(10L, TimeUnit.SECONDS);
            ch.closeFuture().sync();
            if (result == null) {
                String string = null;
                return string;
            }
            String sa = CraftRiseCrypto.decryptWithDefaultKey(result);
            String sa2 = CraftRiseCrypto.base64Decode(sa);
            String sa3 = CraftRiseCrypto.decryptWithDefaultKey(sa2);
            String sa4 = CraftRiseCrypto.decryptWithDefaultKey(sa3);
            String string = sa5 = CraftRiseCrypto.base64Decode(sa4);
            return string;
        } catch (Exception e) {
            String string = null;
            return string;
        } finally {
            group.shutdownGracefully();
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public static String getGlobalSessionHash(final String username, final String password) {
        NioEventLoopGroup group = new NioEventLoopGroup();
        final CompletableFuture future = new CompletableFuture();
        try {
            Bootstrap b = new Bootstrap();
            ((Bootstrap)((Bootstrap)b.group(group)).channel(NioSocketChannel.class)).handler(new ChannelInitializer<SocketChannel>(){

                @Override
                protected void initChannel(SocketChannel ch) {
                    ChannelPipeline pipeline = ch.pipeline();
                    pipeline.addLast(new ObjectDecoder(ClassResolvers.softCachingResolver(ClassLoader.getSystemClassLoader())));
                    pipeline.addLast(new ObjectEncoder());
                    pipeline.addLast(new SimpleChannelInboundHandler<Object>(){

                        @Override
                        public void channelActive(ChannelHandlerContext ctx) {
                            HashMap<String, String> payload = AuthPayloadBuilder.buildPayload(username, password);
                            String json = String.format("{\n  \"messageType\": \"tryLogin\",\n  \"datas\": {\n    \"sumBigX\": \"%s\",\n    \"password\": \"%s\",\n    \"sumBig\": \"%s\",\n    \"sumBigY\": \"%s\",\n    \"sum\": \"%s\",\n    \"key\": \"%s\",\n    \"username\": \"%s\",\n    \"staticSessionKey\": \"%s\"\n  }\n}", payload.get("sumBigX"), password, payload.get("sumBig"), payload.get("sumBigY"), payload.get("sum"), payload.get("key"), username, payload.get("staticSessionKey"));
                            ctx.writeAndFlush(json + "\n");
                        }

                        @Override
                        protected void channelRead0(ChannelHandlerContext ctx, Object msg) {
                            if (msg instanceof String) {
                                String jsonStr = (String)msg;
                                try {
                                    JsonObject obj = new JsonParser().parse(jsonStr).getAsJsonObject();
                                    if (obj.has("globalSessionHash")) {
                                        String hash = obj.get("globalSessionHash").getAsString();
                                        future.complete(hash);
                                    } else if (obj.has("message")) {
                                        future.complete(null);
                                    } else {
                                        future.complete(null);
                                    }
                                } catch (Exception e) {
                                    future.complete(null);
                                }
                                ctx.close();
                            }
                        }

                        @Override
                        public void exceptionCaught(ChannelHandlerContext ctx, Throwable cause) {
                            future.complete(null);
                            ctx.close();
                        }
                    });
                }
            });
            Channel ch = b.connect("185.255.92.10", 4754).sync().channel();
            String result = (String)future.get(10L, TimeUnit.SECONDS);
            ch.closeFuture().sync();
            String string = result;
            return string;
        } catch (Exception e) {
            String string = null;
            return string;
        } finally {
            group.shutdownGracefully();
        }
    }
}

